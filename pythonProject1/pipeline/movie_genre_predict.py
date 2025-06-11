import pandas as pd
import torch
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import mysql.connector
import json

from pythonProject1.config_sql import DB_CONFIG_SQL

# Load a strong context-aware embedding model
print("initialising")
model = SentenceTransformer("all-mpnet-base-v2")
print("initialised")
tqdm.pandas()

# Connect to MySQL and fetch movie data
def get_movies_from_db():
    conn = mysql.connector.connect(
       **DB_CONFIG_SQL
    )
    query = "SELECT id, title, overview FROM movies"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Genre definitions with example descriptions for context (could be expanded or refined)
genre_examples = {
    "action": "explosions, fights, chases, high-stakes missions, heroes vs villains, gunfire, stunts, intense, rescue, conflict, warzone, brawl, shootout, armor, adrenaline, military, weapons, combat, revenge",
    "romance": "love, relationship, heartbreak, emotional, passionate, couple, affair, intimacy, date, chemistry, wedding, feelings, soulmate, kiss, romance novel, desire, longing, connection, romantic",
    "comedy": "funny, humorous, laughter, jokes, light-hearted, satire, parody, awkward, quirky, amusing, clown, punchline, laugh-out-loud, slapstick, ridiculous, stand-up, absurd, silly, entertaining",
    "horror": "ghosts, haunted, scary, supernatural, killer, fear, blood, gore, nightmare, monster, scream, panic, dark, possessed, evil, creepy, fright, demon, chilling, curse",
    "thriller": "suspense, tension, mystery, danger, psychological, killer, twist, espionage, high stakes, pursuit, double-cross, paranoia, crime, stalker, danger, fast-paced, secrets, deception, dark",
    "sci-fi": "space, future, technology, alien, time travel, robot, artificial intelligence, dystopia, teleportation, virtual reality, clone, interstellar, mutation, android, parallel universe, dimension, sci-fi weaponry, extraterrestrial, cyberpunk",
    "drama": "emotional, real life, struggles, family, personal journey, internal conflict, relationship, trauma, heartbreak, tragedy, serious, character-driven, poignant, social issue, depth, transformation, introspection, resolution, loss",
    "fantasy": "magic, mythical, wizards, dragons, otherworldly, enchanted, demi-gods, ancient prophecy, quest, creatures, spells, alternate realm, sword, kingdom, prophecy, fairytale, portal, chosen one, magical artifact",
    "crime": "detective, criminal, investigation, mafia, murder, heist, law enforcement, evidence, witness, corruption, underworld, case, trial, prosecutor, suspect, forensic, alibi, justice, interrogation",
    "adventure": "journey, quest, exploration, exotic locations, danger, expedition, treasure, travel, wilderness, discovery, obstacle, hero, path, challenge, compass, relic, map, tribe, uncharted",
    "documentary": "real events, factual, interviews, educational, historical, analysis, non-fiction, research, biography, environmental, expose, social issue, footage, witness, expert, narration, data, commentary, insight",
    "biography": "life story, real person, achievements, legacy, personal journey, rise to fame, timeline, struggles, memoir, profession, influence, inspiration, milestones, background, notable, transformation, conflict, role model, leadership",
    "animation": "cartoons, animated, CGI, visual storytelling, colorful, voice-over, family-friendly, drawn, motion capture, characters, frame, 2D, 3D, stylized, animals, magical, fantasy, expressions, vibrant, children",
    "family": "suitable for all ages, family values, kids and parents, bonding, love, simple story, relatable, moral, innocent, togetherness, caring, safe, home, warmth, tradition, parenting, unity, holiday, childhood",
    "musical": "songs, singing, dance, musical performance, rhythm, melody, chorus, orchestra, harmony, stage, lyrics, tune, score, Broadway, choreography, soundtrack, emotional singing, showtime, instruments",
    "mystery": "whodunit, puzzling events, secrets, detectives, solving, clue, twist, investigation, enigma, unexpected, hidden, suspense, unanswered, logic, strange events, theories, conspiracy, trail, reveal",
    "war": "battle, military, historical conflicts, soldiers, patriotism, gunfire, trench, army, strategy, sacrifice, uniform, command, fight, bravery, casualties, mission, victory, occupation, history",
    "western": "cowboys, wild west, gunslingers, frontier justice, horses, saloon, sheriff, desert, duels, hat, ranch, revenge, outlaws, gold rush, standoff, prairie, posse, dusty, wanted posters",
    "history": "past events, historical accuracy, real stories, period drama, revolution, legacy, monarchs, ancient, timeline, biography, reenactment, factual, cultural, influential, empire, civilization, war, heritage, tradition",
    "kids": "child-friendly, animated, playful, moral lessons, fun, colorful, animals, adventure, happy ending, songs, jokes, magic, friendship, simple plot, innocence, school, imagination, fairy tale, positive",
    "superhero": "superpowers, comic books, marvel, dc, saving the world, masked vigilantes, flying, strength, justice, origin story, villains, costume, team-up, nemesis, gadgets, secret identity, city under threat, mutant, action-packed",
    "slasher/gore": "bloody, intense violence, killing spree, knives, serial killer, decapitation, brutal, chainsaw, scream queen, shock, splatter, survival horror, torture, body horror, dismemberment, sadistic, murder scenes, explicit",
    "feel-good": "heartwarming, uplifting, emotional, charming, wholesome, joyful, healing, positivity, happy ending, connection, cozy, comfort, smiles, inspiration, pleasant, simple pleasures, bonding, overcoming odds",
    "sports": "athlete, competition, team, match, game, training, championship, underdog, sportsmanship, rivalry, victory, defeat, sweat, physical, race, goal, tournament, performance, teamwork",
    "survival": "stranded, isolation, nature, wilderness, life or death, escape, resilience, endurance, challenge, danger, disaster, lost, fight to live, harsh, instinct, solitude, survival skills, extreme conditions"
}


# Embed genre examples
genre_embeddings = {
    genre: model.encode(desc, convert_to_tensor=True)
    for genre, desc in genre_examples.items()
}



# Main processing
print("hi")
df = get_movies_from_db()
descriptions = df['overview'].tolist()
description_embeddings = model.encode(descriptions, convert_to_tensor=True, batch_size=32, show_progress_bar=True)

# Compute predicted genres for each description embedding
predicted = []
for emb in tqdm(description_embeddings, desc="Classifying genres"):
    scores = {
        genre: util.cos_sim(emb, genre_emb).item()
        for genre, genre_emb in genre_embeddings.items()
    }
    sorted_genres = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    filtered_genres = [g for g, s in sorted_genres if s >= 0.31]
    predicted.append(filtered_genres[:3] if filtered_genres else [sorted_genres[0][0]])

# Save to dataframe
df['predicted_genres'] = predicted

# Save results
out_df = df[['id', 'title', 'predicted_genres']]
def insert_predicted_genres_to_db(df):
    conn = mysql.connector.connect(
        **DB_CONFIG_SQL
    )
    cursor = conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS predicted_movie_genres (
                movie_id INT PRIMARY KEY,
                title TEXT,
                predicted_genres TEXT
            )""")

    values = [
        (row['id'], row['title'], json.dumps(row['predicted_genres']))
        for _, row in df.iterrows()
    ]

    # Split into batches for bulk insert
    batch_size = 100
    for i in tqdm(range(0, len(values), batch_size), desc="Inserting into DB"):
        batch = values[i:i + batch_size]
        insert_query = """
                INSERT INTO predicted_movie_genres (movie_id, title, predicted_genres)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    predicted_genres = VALUES(predicted_genres)
            """
        cursor.executemany(insert_query, batch)
        conn.commit()

    cursor.close()
    conn.close()


insert_predicted_genres_to_db(out_df)
print("Genre prediction complete. Inserted into database table 'predicted_movie_genres'.")

insert_predicted_genres_to_db(out_df)
print("Genre prediction complete. Inserted into database table 'predicted_movie_genres'.")
