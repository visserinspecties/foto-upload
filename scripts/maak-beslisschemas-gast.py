# Maakt beslisschemas-gast.html uit beslisschemas.html (zonder inlog-knop; OneDrive via bestaande inlog van andere tools)
import sys
s=open('beslisschemas.html',encoding='utf-8').read()
def rep(old,new):
    global s
    assert s.count(old)==1,(s.count(old),old[:70]); s=s.replace(old,new)
rep("<title>Beslisschema's ISSO 82.1</title>","<title>Beslisschema's ISSO 82.1 (gast)</title>")
rep('<script src="assets/home-knop.js" defer></script>\n<script src="assets/login.js"></script>\n','')
rep('</div></div>\n\n<script>\n(function(){','</div></div>\n\n<script>window.GAST=true;</script>\n<script>\n(function(){')
rep("else zetBalk('fout','Niet ingelogd bij OneDrive.',[['Inloggen',()=>VILogin.naarInlog()],opnieuw]); return; }",
    "else zetBalk('fout','Niet ingelogd bij OneDrive. Open Huismaten of de Projectmap-app, tik daar op “Inloggen” en kom dan hier terug.',[opnieuw]); return; }")
rep("catch(e){ if(confirm('Niet ingelogd bij OneDrive. Nu inloggen?')) VILogin.naarInlog(); return; }",
    "catch(e){ toast('Niet ingelogd bij OneDrive — log in via Huismaten of de Projectmap-app'); return; }")
open('beslisschemas-gast.html','w',encoding='utf-8').write(s)
