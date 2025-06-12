# TODO

## GUI implementierung:

- Farbfilter und Kamerabilder in das GUI integrieren
    - [Beispiel](/GUI_example.png)
        - Ich sollte auch ein "Tab design" umsetzen, so dass man seinen Bereich auf der rechten Seite auswählen kann
        - Den Nightmode selector links unten find ich auch gut

- Manuelle Steuerung in GUI integrieren

## Next:

- Mehr settings
    - Toggle für connection zum Pi

- Vielleicht muss ich den Toggle noch kleiner machen

- Ich sollte für die Verbindung zum Roboter noch einen toggle in die Settings machen

- Mein Color Scheme stimmt noch nicht
    - Dark Theme richtig auf die Farben im Logo anpassen
    - Light Theme wie die Webpage

- Menüoption "Lagerverwaltung"
    - Anzeigen der Füllstände
        - Vier farbige vertikale Balken
    - Editieren der Füllstände
        - Wenn ein Würfel mal runterfällt oder der Turm kippt

## Test:

- Manuelle Steuerung testen
    - Roboter anschließen und Befehle testen

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

- Die Bilder im GUI sind unscharf