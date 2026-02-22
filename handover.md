Kontekst for AI:
Du er en senior logistik-analytiker og Python/Streamlit-udvikler. Vi arbejder på et projekt kaldet "Bring Nordic Master-Beregner". Det er et internt salgsværktøj, der hjælper sælgere med at uploade kundens nuværende Bring-fakturaer (CSV) og lynhurtigt simulere prisen på en ny aftale (fra enhedspriser til vægt- og zonebaserede matricer).

Projektets nuværende status:
Vi har bygget en fuldt funktionel Streamlit-app (app.py), der understøtter multi-upload, faner pr. land (DK, SE, NO, FI), interaktive priseditorer, heatmap over pakkemix og samlede nordiske konsekvensberegninger.

Kerne-logik og Forretningsregler (VIGTIGT AT HUSKE):

0-kilos reglen: Hvis vægten er 0 kg, eller den gamle pris er 0 kr, skal den gamle pris bevares (dette er gebyrer, told, info-linjer).

Zone-mapping: Postnumre mappes automatisk til zoner.

SE: 00-10=CITY-1, 20-40=CITY-2, Rest=SOUTH-2.

NO: 00-10=OSL, 13-20=NOR2, 40=NOR3, 80=NOR4, 90=NORS.

FI: 00=FI00, 45=FI01, 80=FI02, 94=FI04.

Prismodeller: Sælgeren kan skifte mellem "Enhedspris" (fast pris) og "Vægtbaseret pris" (trappemodel baseret på definerede vægtgrænser pr. land).