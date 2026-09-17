#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

ROOT=Path(__file__).resolve().parents[1]
PRODUCT_PATTERNS=[
('Pendrives','Tecnología',[r'pendrive',r'pen drive',r'memoria usb',r'usb memory']),
('Power Banks','Tecnología',[r'power ?bank',r'bateria externa',r'cargador portatil']),
('Audífonos y Auriculares','Tecnología',[r'audifon',r'auricular']),
('Parlantes','Tecnología',[r'parlante',r'altavoz',r'speaker']),
('Mouse y Teclados','Tecnología',[r'\bmouse\b',r'teclado']),
('Cables y Adaptadores','Tecnología',[r'\bcable\b',r'adaptador',r'\bhub\b']),
('Cargadores','Tecnología',[r'cargador']),
('Soportes para Dispositivos','Tecnología',[r'soporte.*(celular|telefono|tablet)',r'porta.*(celular|telefono)']),
('Linternas','Tecnología',[r'linterna']),('Relojes','Tecnología',[r'\breloj']),
('Mugs y Tazas','Hogar y Bebidas',[r'\bmug',r'\btaza',r'\btazon']),
('Botellas','Hogar y Bebidas',[r'botella']),('Termos','Hogar y Bebidas',[r'\btermo']),
('Accesorios de Vino','Hogar y Bebidas',[r'sacacorcho',r'\bvino\b',r'vinero']),
('Difusores y Aromatizadores','Hogar y Bebidas',[r'difusor',r'aromatiz']),
('Cuidado Personal','Hogar y Bebidas',[r'belleza',r'cosmetic',r'manicur',r'cuidado personal']),
('Libretas y Cuadernos','Oficina y Escritura',[r'libreta',r'cuaderno',r'agenda',r'memo set',r'notebook']),
('Lápices y Bolígrafos','Oficina y Escritura',[r'lapiz',r'lapices',r'boligraf',r'\bpluma\b',r'portaminas']),
('Carpetas y Portafolios','Oficina y Escritura',[r'carpeta',r'portafolio']),
('Llaveros','Promocionales',[r'llavero']),('Lanyards','Promocionales',[r'lanyard',r'portacredencial',r'porta credencial']),
('Antiestrés','Promocionales',[r'antiestres',r'anti stress']),('Abanicos','Promocionales',[r'abanico']),
('Imanes','Promocionales',[r'\biman',r'magnet']),('Paraguas','Promocionales',[r'paraguas']),
('Pelotas','Promocionales',[r'\bpelota']),('Juegos','Promocionales',[r'\bjuego',r'naipes',r'dado']),
('Bolsas','Bolsos y Viaje',[r'\bbolsa',r'\btote\b']),('Mochilas','Bolsos y Viaje',[r'mochila']),
('Coolers','Bolsos y Viaje',[r'cooler']),('Bananos','Bolsos y Viaje',[r'\bbanano']),
('Billeteras y Portadocumentos','Bolsos y Viaje',[r'billetera',r'portadocument',r'tarjetero']),
('Maletines y Fundas','Bolsos y Viaje',[r'maletin',r'\bfunda']),('Bolsos de Viaje','Bolsos y Viaje',[r'bolso.*viaje']),
('Bolsos','Bolsos y Viaje',[r'\bbolso']),('Accesorios de Viaje','Bolsos y Viaje',[r'almohada.*viaje',r'identificador.*equipaje']),
('Accesorios de Automóvil','Herramientas y Outdoor',[r'parasol',r'automovil',r'auto ',r'vehiculo']),
('Artículos Deportivos','Herramientas y Outdoor',[r'frisbee',r'deportiv']),
('Herramientas','Herramientas y Outdoor',[r'herramient',r'\basado\b',r'\bbbq\b',r'barbecue']),
('Delantales','Textil',[r'delantal']),('Gorras y Sombreros','Textil',[r'gorra',r'sombrero']),
('Poleras','Textil',[r'polera',r'camiseta']),('Toallas y Textil Hogar','Textil',[r'toalla']),
('Chaquetas y Polar','Textil',[r'chaqueta',r'\bpolar\b']),
('Medallas, Trofeos y Galvanos','Premios y Reconocimientos',[r'medalla',r'trofeo',r'galvano',r'premio corporativo']),
('Sets de Regalo','Sets de Regalo',[r'set de regalo',r'gift set']),('Packaging','Packaging',[r'packaging',r'empaque corporativo']),
]
GROUP_FALLBACK={
'Agendas Libretas Memo Set':('PRODUCTO','Oficina y Escritura','Libretas y Cuadernos',''),
'Asado BBQ':('PRODUCTO','Herramientas y Outdoor','Herramientas',''),
'Asado y BBq #2':('PRODUCTO','Herramientas y Outdoor','Herramientas',''),
'Asado y BBq - delantales':('PRODUCTO','Textil','Delantales',''),
'Asado y BBq - para':('PRODUCTO','Herramientas y Outdoor','Herramientas',''),
'Asado y BBq - set':('PRODUCTO','Herramientas y Outdoor','Herramientas',''),
'Bolsas Ecológicas':('PRODUCTO','Bolsos y Viaje','Bolsas',''),
'Bolsas TNT':('PRODUCTO','Bolsos y Viaje','Bolsas',''),
'Boligrafos y Lápices':('PRODUCTO','Oficina y Escritura','Lápices y Bolígrafos',''),
'Lapices':('PRODUCTO','Oficina y Escritura','Lápices y Bolígrafos',''),
'Lanyard Portacredencial':('PRODUCTO','Promocionales','Lanyards',''),
'Llaveros':('PRODUCTO','Promocionales','Llaveros',''),
'Llaveros Metalicos #2':('PRODUCTO','Promocionales','Llaveros',''),
'Llaveros Metalicos #3':('PRODUCTO','Promocionales','Llaveros',''),
'Llaveros Metalicos - grabados':('PRODUCTO','Promocionales','Llaveros',''),
'Llaveros Metalicos - personalizados':('PRODUCTO','Promocionales','Llaveros',''),
'Llaveros Metalicos - publicitarios':('PRODUCTO','Promocionales','Llaveros',''),
'Parasol Carton':('PRODUCTO','Herramientas y Outdoor','Accesorios de Automóvil',''),
'Pelotas Antiestres':('PRODUCTO','Promocionales','Antiestrés',''),
'Pen Drive':('PRODUCTO','Tecnología','Pendrives',''),
'Power Bank':('PRODUCTO','Tecnología','Power Banks',''),
'Día de la Madre':('USO_CAMPAÑA','','','Día de la Madre'),
'FIn de Año':('USO_CAMPAÑA','','','Fin de Año'),
'Descanso y Diversión':('USO_CAMPAÑA','','','Ocio y Pasatiempo'),
'Verano':('USO_CAMPAÑA','','','Verano'),
'Promocionales':('USO_CAMPAÑA','','','Promocionales'),
'Regalos Publicitarios':('USO_CAMPAÑA','','','Regalos corporativos'),
'Tecnologicos':('USO_CAMPAÑA','Tecnología','','Tecnología'),
'Bamboo':('USO_CAMPAÑA','','','Bamboo'),
'Mugs, Botellas y Termos..':('USO_CAMPAÑA','Hogar y Bebidas','','Bebidas'),
}
BAD_GROUPS={'','--'}
TECHNICAL_GROUPS={'AdGroup ID: 29852379151 Created at 2016-06-13T05:28:10.432-07:00'}

def norm(s:str)->str:
 s=(s or '').strip().strip('"').replace('+',' ')
 s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).lower()
 return re.sub(r'\s+',' ',s)

def classify(keyword,group):
 text=norm(keyword)
 if not text: return ('DESCARTAR','','','','fila vacía','HIGH')
 if group in BAD_GROUPS: return ('DESCARTAR','','','','grupo técnico/vacío','HIGH')
 for family,macro,patterns in PRODUCT_PATTERNS:
  if any(re.search(p,text) for p in patterns): return ('PRODUCTO',macro,family,'','keyword→objeto','HIGH')
 if group in TECHNICAL_GROUPS:
  if any(x in text for x in ['regalo','corporativ','publicitari','promocional','empresa','merchandising','articulos','productos']):
   return ('USO_CAMPAÑA','','','Genérico corporativo','keyword rescatada de grupo técnico','MEDIUM')
 if group in GROUP_FALLBACK:
  c,macro,fam,theme=GROUP_FALLBACK[group]
  conf='MEDIUM' if c=='PRODUCTO' else 'MEDIUM'
  return (c,macro,fam,theme,'fallback grupo histórico',conf)
 if any(x in text for x in ['regalo','corporativ','publicitari','promocional','empresa','merchandising']):
  return ('USO_CAMPAÑA','','','Genérico corporativo','intención comercial genérica','MEDIUM')
 return ('DESCARTAR','','','','sin objeto ni intención utilizable','LOW')

def url_info(raw):
 raw=(raw or '').strip()
 if not raw:return ('EMPTY','')
 try:u=urlsplit(raw)
 except:return ('INVALID','')
 host=(u.hostname or '').lower()
 if host not in {'regalospremium.cl','www.regalospremium.cl'}:return ('EXTERNAL_OR_INVALID','')
 safe=urlunsplit(('https','regalospremium.cl',u.path or '/',u.query,''))
 if 'index.php' in u.path:return ('LEGACY_VIRTUEMART',safe)
 if u.path.startswith('/busqueda'):return ('INTERNAL_SEARCH',safe)
 if '√' in raw:return ('INVALID', '')
 if u.scheme!='https':return ('LEGACY_HTTP',safe)
 if host.startswith('www.'):return ('WWW_VARIANT',safe)
 return ('CURRENT_FORMAT',safe)

def num(v):
 s=(v or '').strip().replace('.','').replace(',','.')
 try:return float(s)
 except:return 0.0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);a=ap.parse_args()
 src=Path(a.source)
 with src.open(encoding='utf-8-sig',newline='') as f:
  f.readline();f.readline();rows=list(csv.DictReader(f))
 buckets=defaultdict(list)
 for r in rows:buckets[(r['Palabra clave'].strip().lower(),r['Tipo de concordancia'].strip(),r['Grupo de anuncios'].strip())].append(r)
 out=[]; urls=Counter(); url_status=Counter()
 for k,rs in buckets.items():
  hist=sorted({r.get('URL final','').strip() for r in rs if r.get('URL final','').strip()})
  for u in hist:
   urls[u]+=1;url_status[url_info(u)[0]]+=1
  c,macro,fam,theme,method,conf=classify(rs[0]['Palabra clave'],rs[0]['Grupo de anuncios'].strip())
  statuses=sorted({url_info(u)[0] for u in hist}) if hist else ['EMPTY']
  normalized=sorted({url_info(u)[1] for u in hist if url_info(u)[1]})
  out.append({
   'keyword':rs[0]['Palabra clave'].strip(),'match_type':rs[0]['Tipo de concordancia'].strip(),'ad_group':rs[0]['Grupo de anuncios'].strip(),
   'keyword_state':rs[0].get('Estado de las palabras clave',''),'serving_state':rs[0].get('Estado',''),
   'historical_urls':' | '.join(hist),'normalized_urls':' | '.join(normalized),'url_statuses':' | '.join(statuses),'url_conflict':'YES' if len(hist)>1 else 'NO',
   'intent_class':c,'macroarea':macro,'familia':fam,'intent_theme':theme,'classification_method':method,'classification_confidence':conf,
   'impressions_max':int(max(num(r.get('Impr.')) for r in rs)),'clicks_max':int(max(num(r.get('Clics')) for r in rs)),
   'conversions_max':max(num(r.get('Conversiones')) for r in rs),'source_rows':len(rs)
  })
 out.sort(key=lambda x:(x['ad_group'].lower(),norm(x['keyword']),x['match_type']))
 d=ROOT/'data/ads';d.mkdir(parents=True,exist_ok=True)
 fields=list(out[0]);
 with (d/'ads_intent_mapping.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
 # group summary
 gs=[]
 for g in sorted({x['ad_group'] for x in out}):
  rr=[x for x in out if x['ad_group']==g]; cc=Counter(x['intent_class'] for x in rr); fam=Counter(x['familia'] for x in rr if x['familia'])
  gs.append({'ad_group':g,'keywords':len(rr),'producto':cc['PRODUCTO'],'uso_campana':cc['USO_CAMPAÑA'],'descartar':cc['DESCARTAR'],'top_family':fam.most_common(1)[0][0] if fam else '','families_detected':len(fam)})
 with (d/'ads_group_mapping.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=gs[0].keys());w.writeheader();w.writerows(gs)
 # URL inventory
 inv=[]
 for u,n in urls.most_common():
  st,nu=url_info(u);inv.append({'historical_url':u,'normalized_url':nu,'status':st,'keyword_keys':n})
 with (d/'ads_url_inventory.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['historical_url','normalized_url','status','keyword_keys']);w.writeheader();w.writerows(inv)
 unique_status=Counter(url_info(u)[0] for u in urls)
 summary={'source':src.name,'source_rows':len(rows),'unique_keyword_keys':len(out),'duplicates_collapsed':len(rows)-len(out),'ad_groups':len(gs),'intent_counts':dict(Counter(x['intent_class'] for x in out)),'confidence_counts':dict(Counter(x['classification_confidence'] for x in out)),'url_reference_status_counts':dict(url_status),'unique_url_status_counts':dict(unique_status),'unique_historical_urls':len(urls),'url_conflicts':sum(x['url_conflict']=='YES' for x in out)}
 rp=ROOT/'reports/ads';rp.mkdir(parents=True,exist_ok=True);(rp/'ads_mapping_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
