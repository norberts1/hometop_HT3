hometop_HT3
===========

Everything needed to be shown at your 'hometop'.

Dieses repo kann NICHT alle Wuensche erfuellen, die man an einen 'hometop' stellen könnte.
Jeder hat seine Vorstellungen wie das 'home' 'top' werden kann. 
Sicher ist die Präsentation von Informationen aus dem eigenen 'Heim' ein Wunsch, der keiner bleiben muß.
Viele Projekte arbeiten daran z.B. 'FHEM' (www.fhem.de) für die Steuerung und Präsentation von Schalt- und Messaktoren.

Dieses repo beschränkt sich auf die Erfassung/(Steuerung) und Präsentation von Heizungs- und Solar-Informationen.
Zur Zeit ist die Erfassung für Heizungsanlagen der Firma 'Junkers' und dem Bus 'Heatronic3 (c)' ausgelegt.
Diese Einschränkung muss und soll nicht so bleiben (frei nach dem Motto: andere Hersteller haben auch schöne Busse).
Daher ist die Struktur der Software und Datenhaltung darauf angelegt eben möglichst neutral zu sein.
Klar die Decodierung ist protokollabhängig, jedoch die Datenhaltung ist den Systemeigenschaften (Systemparts) zugeordnet.
Z.B. hat jedes System mindestens ein 'Heizgerät' und 'Heizkreis' mit 'Warmwasser'-Erzeugung und eventuell noch 'Solar' und
vielleicht noch eine Wärmepumpe. 
Dies ist recht Hersteller unabhängig und nur abhängig davon was der Kunde will.
Ja manchmal will der wohl auch, daß alle Hersteller einen einheitlichen Bus mit einheitlichem Protokoll haben, 
aber davon kann mal wohl nur träumen.

Um diesem Ziel trotzdem ein wenig näher zu kommen ist dieses repo entstanden. 
Letztendlich ist es nur eine Frage der 'Adaption' und 'Dekodierung' um die erfassten Daten in einer Datenbank zu versenken und daraus eine ansprechende Präsentation zu machen.

Jeder, der an diesem Ziel mitarbeiten will ist herzlich willkommen. 
Wenn schon die Hersteller sich nicht einig sind so kann zumindest der Kunde seine Ziele bearbeiten und erreichen.

Wichtiger Hinweis:
Der Nachbau und die Inbetriebnahme der Adaptionen ist auf eigene Gefahr und die Beschreibung und die Software erheben nicht den Anspruch auf Vollständigkeit.
Eine Änderung an Software-Modulen und Hardware-Beschreibungen ist jederzeit ohne Vorankündigung möglich.
Gewährleistung, Haftung und Ansprüche durch Fehlfunktionen an Heizung oder Adaption sind hiermit ausdrücklich ausgeschlossen.
