"""Add contextual quotation links without changing product facts or URLs.

Dry run by default. Uses existing hosting credentials locally, never prints them.
Backups and optimistic predicates protect pre-existing descriptions.
"""
import argparse
import datetime
import html
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import urlencode

MARKER = 'data-rp-quote="20261015"'
GENERIC = 'pensado para empresas que buscan un regalo corporativo útil, presentable y fácil de integrar en campañas, eventos, kits de bienvenida o acciones de fidelización.'
GENERIC_TAIL = ' Su formato facilita una presencia de marca permanente en el uso diario y permite personalización con logo según la técnica compatible con el material.'


def remove_generic_opening(text, name):
    """Remove only the two verified boilerplate variants; retain product facts."""
    match = re.search(r'<p\b[^>]*>(.*?)</p>', text, flags=re.S | re.I)
    if match:
        plain = html.unescape(re.sub(r'<[^>]+>', '', match.group(1))).strip()
        heading = re.search(r'<h2\b[^>]*>(.*?)</h2>', text, flags=re.S | re.I)
        names = {name}
        if heading:
            names.add(html.unescape(re.sub(r'<[^>]+>', '', heading.group(1))).strip())
        if any(plain in (n + ' ' + GENERIC, n + ' ' + GENERIC + GENERIC_TAIL) for n in names):
            return text[:match.start()] + text[match.end():]
    return text


def quotation_links(name, reference, url, product_id):
    message = f"Hola, quisiera cotizar {name} (referencia {reference}). {url}\nCantidad: \nFecha requerida: "
    whatsapp = 'https://wa.me/56944280900?' + urlencode({'text': message})
    email = 'mailto:ventas@regalospremium.cl?' + urlencode({'subject': f'Cotización {reference} — {name}', 'body': message})
    def link(href, label, primary=False):
        style = 'display:inline-block;box-sizing:border-box;max-width:100%;min-height:44px;padding:12px 16px;margin:4px 8px 4px 0;border:1px solid #174b78;border-radius:4px;font-size:15px;font-weight:600;line-height:20px;white-space:normal;'
        style += 'background:#174b78;color:#fff;' if primary else 'background:#fff;color:#174b78;'
        return f'<a href="{html.escape(href, quote=True)}" style="{style}">{label}</a>'
    return f'<div {MARKER} aria-label="Solicitar cotización" style="margin:12px 0;">' + link(whatsapp, 'Cotizar este producto por WhatsApp', True) + link(email, 'Cotizar por correo') + '</div>'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--parameters', required=True)
    ap.add_argument('--host', required=True)
    ap.add_argument('--catalog', required=True)
    ap.add_argument('--backup-dir', required=True)
    ap.add_argument('--product-id', type=int)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    source = Path(args.parameters).read_text()
    def value(key):
        match = re.search(r"'" + key + r"'\s*=>\s*'([^']*)'", source)
        if not match:
            raise ValueError('Missing configuration key')
        return match.group(1)
    def quoted(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    fd, config = tempfile.mkstemp(prefix='rp-quote-', suffix='.cnf')
    os.fchmod(fd, 0o600)
    password = value('database_password')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write('[client]\nhost=' + args.host + '\nuser=' + quoted(value('database_user')) + '\npassword=' + quoted(password) + '\nconnect-timeout=5\nprotocol=tcp\n')
        def sql(statement):
            result = subprocess.run(['mariadb', '--defaults-extra-file=' + config, '--skip-ssl', '--batch', '--raw', '--skip-column-names', value('database_name')], input=statement, text=True, capture_output=True, timeout=90)
            if result.returncode:
                raise RuntimeError(result.stderr.replace(password, '[REDACTED]')[:600])
            return result.stdout
        engines = sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('ps_product_lang','ps_st_easy_content_lang');").splitlines()
        if len(engines) != 2 or set(engines) != {'InnoDB'}:
            raise RuntimeError('Transactional table requirement failed')
        rows = [json.loads(line) for line in sql("SELECT JSON_OBJECT('id',pl.id_product,'name',pl.name,'reference',p.reference,'description_short',pl.description_short) FROM ps_product_lang pl JOIN ps_product_shop ps ON ps.id_product=pl.id_product AND ps.id_shop=pl.id_shop JOIN ps_product p ON p.id_product=pl.id_product WHERE ps.active=1 AND pl.id_shop=1 AND pl.id_lang=1;").splitlines()]
        import csv
        catalog = {int(r['product_id']): r['url'] for r in csv.DictReader(Path(args.catalog).open(encoding='utf-8-sig'))}
        if set(catalog) != {r['id'] for r in rows} or len(rows) != 1309:
            raise RuntimeError('Live/catalog coverage mismatch')
        if args.product_id:
            rows = [r for r in rows if r['id'] == args.product_id]
            if len(rows) != 1:
                raise RuntimeError('Pilot product missing')
        updates = []
        backups = []
        generic_removed = 0
        def hexvalue(text):
            return "CONVERT(0x" + text.encode().hex() + " USING utf8mb4)"
        for row in rows:
            old = row['description_short'] or ''
            clean = re.sub(r'<div data-rp-quote="20261015"[^>]*>.*?</div>', '', old, count=1, flags=re.S)
            cleaned = remove_generic_opening(clean, row['name'])
            generic_removed += cleaned != clean
            clean = cleaned
            new = clean + quotation_links(row['name'], row['reference'], catalog[row['id']], row['id'])
            if old == new:
                continue
            where = f"id_product={row['id']} AND id_shop=1 AND id_lang=1"
            updates.append('UPDATE ps_product_lang SET description_short=' + hexvalue(new) + ' WHERE ' + where + ' AND HEX(COALESCE(description_short,\'\'))=\'' + old.encode().hex().upper() + "';")
            backups.append({'table': 'ps_product_lang', 'where': where, 'old': old, 'new': new})
        footer = json.loads(sql("SELECT JSON_OBJECT('text',text) FROM ps_st_easy_content_lang WHERE id_st_easy_content=5 AND id_lang=1;").strip())['text']
        if not args.product_id and 'data-rp-contact="20261015"' not in footer:
            new = footer.replace('Teléfono: +56 9 44280900', '<a href="tel:+56944280900">Teléfono: +56 9 44280900</a>')
            new += '<div data-rp-contact="20261015"><p><a href="https://wa.me/56944280900">Cotizar por WhatsApp</a> · <a href="https://regalospremium.cl/contactenos">Solicitar cotización</a></p><p><a href="https://regalospremium.cl/regalos-corporativos/">Regalos corporativos</a> · <a href="https://regalospremium.cl/regalos-publicitarios/">Regalos publicitarios</a></p></div>'
            updates.append('UPDATE ps_st_easy_content_lang SET text=' + hexvalue(new) + " WHERE id_st_easy_content=5 AND id_lang=1 AND HEX(text)='" + footer.encode().hex().upper() + "';")
            backups.append({'table': 'ps_st_easy_content_lang', 'where': 'id_st_easy_content=5 AND id_lang=1', 'old': footer, 'new': new})
        report = {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'mode': 'apply' if args.apply else 'dry-run', 'products_reviewed': len(rows), 'product_updates': sum(r['table']=='ps_product_lang' for r in backups), 'generic_openings_removed': generic_removed, 'footer_updates': sum(r['table']=='ps_st_easy_content_lang' for r in backups)}
        if args.apply and updates:
            backup = Path(args.backup_dir)
            backup.mkdir(parents=True, exist_ok=False)
            os.chmod(backup, 0o700)
            (backup/'before_after.json').write_text(json.dumps(backups, ensure_ascii=False, indent=2))
            restore = ['START TRANSACTION;']
            for r in backups:
                field = 'description_short' if r['table']=='ps_product_lang' else 'text'
                restore.append('UPDATE ' + r['table'] + ' SET ' + field + '=' + hexvalue(r['old']) + ' WHERE ' + r['where'] + ' AND HEX(' + field + ")='" + r['new'].encode().hex().upper() + "';")
            (backup/'restore.sql').write_text('\n'.join(restore + ['COMMIT;']))
            # Optimistic predicates remain active, and every changed row is verified in transaction.
            guards = ['CREATE TEMPORARY TABLE rp_quote_guard (ok INT NOT NULL CHECK(ok=1));']
            for update in updates:
                guards += [update, 'INSERT INTO rp_quote_guard VALUES (ROW_COUNT());']
            sql('START TRANSACTION;\n' + '\n'.join(guards) + '\nCOMMIT;')
            report['backup_dir'] = str(backup)
            report['verified_changed_rows'] = len(updates)
        print(json.dumps(report, ensure_ascii=False))
    finally:
        os.unlink(config)


if __name__ == '__main__':
    main()
