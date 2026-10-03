from pathlib import Path
src=Path("/home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/.htaccess.before_canonical_alt")
out=Path("/home/maxdaguzan/RegalosPremium_Backups/gsc_fix_20261003/.htaccess.canonical_alt")
s=src.read_text(encoding="utf-8")
marker="# BEGIN GSC SURGERY 2026-10-03"
block="""# BEGIN GSC CANONICAL ALIASES 2026-10-03
RewriteRule ^publicitarios-ecofriendly/?$ https://regalospremium.cl/productos-eco-friendly-publicitarios/ [R=301,L,NE]
RewriteRule ^boligrafos-funcionales-y-destacadores/?$ https://regalospremium.cl/boligrafos-funcionales-y-destacadores-publicitarios/ [R=301,L,NE]
RewriteRule ^boligrafos-cuerpo-blanco/?$ https://regalospremium.cl/boligrafos-cuerpo-blanco-publicitarios/ [R=301,L,NE]
RewriteRule ^mugs-termos-sublimacion/?$ https://regalospremium.cl/mugs-y-termos-para-sublimacion-publicitarios/ [R=301,L,NE]
RewriteRule ^boligrafos-cuerpo-color/?$ https://regalospremium.cl/boligrafos-cuerpo-color-publicitarios/ [R=301,L,NE]
RewriteRule ^boligrafos-cuerpo-plateado/?$ https://regalospremium.cl/boligrafos-cuerpo-plateado-publicitarios/ [R=301,L,NE]
# sturls route collision: the public slug resolved category 66 (Cuero) instead of active category 127 (Metalicos).
RewriteRule ^llaveros-metalicos/?$ index.php?id_category=127&controller=category [QSA,L]
# END GSC CANONICAL ALIASES 2026-10-03

"""
if "# BEGIN GSC CANONICAL ALIASES 2026-10-03" in s:
    raise SystemExit("ALREADY_PRESENT")
if marker not in s:
    raise SystemExit("MARKER_MISSING")
out.write_text(s.replace(marker,block+marker,1),encoding="utf-8")
print(out, out.stat().st_size)
