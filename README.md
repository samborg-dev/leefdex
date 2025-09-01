# Pokémon Gen 1 Pokédex Scraper

A simple web scraper that extracts Pokémon information from [Serebii.net](https://www.serebii.net/pokedex/001.shtml) for all 151 Generation 1 Pokémon.

## Features

- Extracts basic Pokémon information (name, number, types, classification, height, weight)
- Gets base stats (HP, Attack, Defense, Special, Speed)
- Collects level-up moves and TM moves separately
- Saves data to JSON format
- Includes respectful delays between requests
- Simple and easy to understand code structure

## Installation

1. Install Python 3.6 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Test the scraper first (recommended)
```bash
python test_scraper.py
```
This will test the scraper on just Bulbasaur (#001) to make sure everything works.

### Scrape all 151 Pokémon
```bash
python pokemon_scraper.py
```
This will scrape all Generation 1 Pokémon and save the data to `gen1_pokedex.json`.

## What the scraper extracts

For each Pokémon, the scraper collects:
- **Basic Info**: Name, Pokédex number, types, classification
- **Physical**: Height and weight (both imperial and metric)
- **Stats**: Base stats (HP, Attack, Defense, Special, Speed)
- **Moves**: Level-up moves (learnset) and TM moves separately

## Output format

The data is saved as a JSON file with this structure:
```json
[
  {
    "name": "Bulbasaur",
    "number": "001",
    "types": ["Grass", "Poison"],
    "classification": "Seed Pokémon",
    "height": {
      "imperial": "2'04\"",
      "metric": "0.7m"
    },
    "weight": {
      "imperial": "15.2lbs",
      "metric": "6.9kg"
    },
    "base_stats": {
      "HP": "45",
      "Attack": "49",
      "Defense": "49",
      "Special": "65",
      "Speed": "45"
    },
    "moves": {
      "learnset": [
        {"level": "—", "name": "Tackle"},
        {"level": "—", "name": "Growl"},
        {"level": "7", "name": "Leech Seed"},
        {"level": "13", "name": "Vine Whip"},
        {"level": "20", "name": "Poison Powder"},
        {"level": "27", "name": "Razor Leaf"},
        {"level": "34", "name": "Growth"},
        {"level": "41", "name": "Sleep Powder"},
        {"level": "48", "name": "Solar Beam"}
      ],
      "tm_moves": [
        {"tm_number": "TM03", "name": "Swords Dance"},
        {"tm_number": "TM06", "name": "Toxic"},
        {"tm_number": "TM08", "name": "Body Slam"},
        {"tm_number": "TM09", "name": "Take Down"},
        {"tm_number": "TM10", "name": "Double-Edge"},
        {"tm_number": "TM20", "name": "Rage"},
        {"tm_number": "TM21", "name": "Mega Drain"},
        {"tm_number": "TM22", "name": "Solar Beam"},
        {"tm_number": "TM31", "name": "Mimic"},
        {"tm_number": "TM32", "name": "Double Team"},
        {"tm_number": "TM33", "name": "Reflect"},
        {"tm_number": "TM34", "name": "Bide"},
        {"tm_number": "TM44", "name": "Rest"},
        {"tm_number": "TM50", "name": "Substitute"},
        {"tm_number": "HM01", "name": "Cut"}
      ]
    }
  }
]
```

## Important notes

- The scraper includes a 1-second delay between requests to be respectful to the website
- It uses a realistic user agent to avoid being blocked
- All data is saved to JSON files for easy processing
- The code is structured to be easy to understand and modify
- Height and weight are separated into imperial and metric measurements
- Moves are categorized into learnset (level-up moves) and TM moves

## Customization

You can easily modify the scraper to:
- Extract additional information (locations, evolution chains, etc.)
- Change the output format
- Add error handling for specific cases
- Modify the delay between requests
- Add more move categories (egg moves, tutor moves, etc.)

## Troubleshooting

If you encounter issues:
1. Make sure you have a stable internet connection
2. Check that all required packages are installed
3. Try running the test script first
4. The website structure might change over time - you may need to update the selectors

## Legal notice

This scraper is for educational purposes. Please respect the website's robots.txt and terms of service. The scraper includes delays to avoid overwhelming the server.