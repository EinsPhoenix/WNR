# TODO

## GUI implementierung:

- Ich will, dass man anfangs mit Tab durch die sidebar geht
    - Wenn man dann enter drückt kommt man in den submenu mode
        - Submenu mode heißt, dass man mit tab nur durch die Elemente im conent_menu schalten kann
        - Mit esc kann man wieder aus dem submenu mode raus

- Farbfilter und Kamerabilder in das GUI integrieren
    - [Beispiel](/GUI_example.png)
        - Ich sollte auch ein "Tab design" umsetzen, so dass man seinen Bereich auf der rechten Seite auswählen kann
        - Den Nightmode selector links unten find ich auch gut

- Manuelle Steuerung in GUI integrieren

## Next:

- Ich könnte "Change speed" zu "Change run vars" oder so ändern
    - Dann kann ich auch während dem Laufen verschiedene Werte für die höhe oder so testen

- Menüoption "Lagerverwaltung"
    - Anzeigen der Füllstände
    - Editieren der Füllstände
        - Wenn ein Würfel mal runterfällt oder der Turm kippt

## Test:

- Manuelle Steuerung testen
    - Roboter anschließen und Befehle testen

- Automatisierung testen
    - Pi / Kamera aufbauen
    - Roboter anschließen
    - Auf Pi laufen lassen:
        - /colorObject/RaspCamStream/Start_Service.py
    - Auf Laptop laufen lassen:
        - /colorObject/Calibration/main.py
        - /WNR/Robot/source/main.py

## Ideas:

- Implement build scripts:
    - Pyramid
    - Circle

- 4 Würfeltürme mit unterschiedlichen Farben sortieren lassen
    - Angabe der Würfel von oben nach unten angeben
    - Lösungsweg berechnen, wie man die mit einem zusätzlichen Turm sortieren kann
    - Mit dem Roboter die Würfel sortieren

- Vielleicht kann ich die Rotation der Würfel bestimmen
    - Dann kann ich die nach dem Aufheben korrigieren und perfekt aufeinander stapeln
    - Vielleicht kann ich auch an einen festen Gegenstand vorfahren und dann um 90° drehen
        - Dann verkantet sich der Würfel mit einer flachen Seite ander Wand und der Saugnapf dreht hoffentlich dann durch

- Ich bastel eine GUI für das Menü

## Fix:

- Ich muss die Werte für die Höhe anpassen
    - Aufheben
    - Zum Lager fahren
    - Abladen

- Anpassen der Lager/Fahrwege
    - Wenn ich mehr als 4 Würfel aufeinander stellen will stirbt der Roboter

- Ich muss das Rausfiltern der bereits gelagerten Würfel umschreiben
    - x > 55 funktioniert nicht
        - Die forderen Würfel, die schon im Lager sind, werden erkannt und als unsortiert gezählt

- TODOs und FIXMEs

- Ich sollte in get_next_block einbauen, dass der Roboter den Sichtbereich frei macht, wenn er keine Würfel mehr findet