#!/usr/bin/env python3
"""
Pokemon Scraper - Main runner script
Imports and runs the appropriate generation scraper
"""

from gen1_scraper import Gen1Scraper

def main():
    """Main function to run the Pokémon scraper"""
    print("Pokémon Scraper")
    print("=" * 20)
    print("Running Generation 1 scraper...")
    print()
    
    scraper = Gen1Scraper()
    scraper.scrape_all()

if __name__ == "__main__":
    main()
