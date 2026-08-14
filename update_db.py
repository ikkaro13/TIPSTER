import sqlite3

conn = sqlite3.connect('backend/tipster.db')
c = conn.cursor()

# Actualizar apuestas viejas genéricas
c.execute("UPDATE bets SET pick = 'Puebla vs Monterrey: ' || pick WHERE id = 'bet_1'")
c.execute("UPDATE bets SET pick = 'Toluca vs America: ' || pick WHERE id = 'bet_2'")
c.execute("UPDATE bets SET pick = 'Chivas vs Cruz Azul: ' || pick WHERE id = 'bet_3'")
c.execute("UPDATE bets SET pick = 'Pumas vs Leon: ' || pick WHERE id = 'bet_5'")

# También cualquier otra que no tenga ":"
c.execute("UPDATE bets SET pick = 'Partido Anterior: ' || pick WHERE pick NOT LIKE '%:%'")

conn.commit()
conn.close()
print("Apuestas viejas actualizadas.")
