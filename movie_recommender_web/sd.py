import csv

# Define the data
movies = [
    ["Title", "Genre", "Overview"],
    ["Inception", "Sci-Fi", "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into a CEO's mind."],
    ["The Dark Knight", "Action", "Batman raises the stakes in his war on crime. With the help of Lt. Jim Gordon and Harvey Dent, he sets out to dismantle organized crime in Gotham."],
    ["Interstellar", "Sci-Fi", "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival."],
    ["The Prestige", "Drama", "Two magicians become rivals in their quest to create the ultimate illusion."],
    ["Memento", "Thriller", "A man with short-term memory loss attempts to track down his wife's murderer."],
    ["Avengers: Endgame", "Action", "After the devastating events of Infinity War, the Avengers assemble once more to reverse Thanos' actions."],
    ["Iron Man", "Action", "After being held captive in an Afghan cave, billionaire engineer Tony Stark creates a unique weaponized suit of armor to fight evil."],
    ["Guardians of the Galaxy", "Action", "A group of intergalactic criminals must pull together to stop a fanatical warrior from taking control of the universe."],
    ["The Matrix", "Sci-Fi", "A hacker discovers that reality as he knows it is a simulation controlled by machines, and joins a rebellion to free humanity."],
    ["Avatar", "Sci-Fi", "A paraplegic Marine dispatched to the moon Pandora on a unique mission becomes torn between following orders and protecting the world he feels is his home."]
]

# Write data to CSV file
with open("movies.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(movies)

print("movies.csv file created successfully!")
