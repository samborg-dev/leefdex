from pokemon_scraper import scrape_pokemon_page, save_to_json
import json

def test_single_pokemon():
    """
    Test the scraper on a single Pokémon page
    """
    print("Testing scraper on Bulbasaur page...")
    
    # Test with Bulbasaur
    url = "https://www.serebii.net/pokedex/001.shtml"
    pokemon_data = scrape_pokemon_page(url)
    
    if pokemon_data:
        print("✓ Successfully scraped Pokémon data!")
        print("\nExtracted data:")
        print(json.dumps(pokemon_data, indent=2, ensure_ascii=False))
        
        # Save test data using the proper folder structure
        save_to_json(pokemon_data, 'test_bulbasaur.json')
        
    else:
        print("✗ Failed to scrape Pokémon data")

if __name__ == "__main__":
    test_single_pokemon()
