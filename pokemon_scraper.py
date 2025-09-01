import requests
from bs4 import BeautifulSoup
import time
import json
import re
import os
from urllib.parse import urljoin

def download_image(url, local_path):
    """
    Download an image from URL to local path
    """
    try:
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def scrape_pokemon_page(url):
    """
    Scrape a single Pokémon page from Serebii.net
    """
    try:
        # Add a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Pokémon information
        pokemon_data = {}
        
        # Get Pokémon name - look for the name in the main info table
        pokemon_name = None
        
        # First, try to find the name in the title
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            if '#' in title_text and '-' in title_text:
                # Extract name from title like "Serebii.net Pokédex - #025 - Pikachu"
                # The name is after the last dash
                parts = title_text.split('-')
                if len(parts) >= 3:
                    # Last part should be the Pokémon name
                    pokemon_name = parts[-1].strip()
                    # Clean up any extra text like "Pokémon" if present
                    if 'Pokémon' in pokemon_name:
                        pokemon_name = pokemon_name.replace('Pokémon', '').strip()
        
        # If we didn't get the name from title, try to find it in the page content
        if not pokemon_name:
            # Look for the main Pokémon name in the page - it's usually in a large heading
            name_heading = soup.find('h1') or soup.find('h2') or soup.find('h3')
            if name_heading:
                heading_text = name_heading.get_text(strip=True)
                # Clean up the heading text
                if heading_text and '#' not in heading_text and 'Pokédex' not in heading_text:
                    pokemon_name = heading_text
        
        # If still no name, try to find it in the main content area
        if not pokemon_name:
            # Look for text that looks like a Pokémon name in the main content
            main_content = soup.find('div', id='content') or soup.find('body')
            if main_content:
                # Find all text nodes and look for Pokémon-like names
                for text_node in main_content.find_all(text=True):
                    text = text_node.strip()
                    if (text and 
                        len(text) > 2 and 
                        len(text) < 20 and  # Pokémon names are typically short
                        not text.isdigit() and 
                        not any(char in text for char in ['#', 'Pokémon', 'lbs', "'", 'm', 'kg', 'Points', 'Hit Points', 'Attack', 'Defense', 'Special', 'Speed', 'Gift', 'Route', 'Scratch']) and
                        not text.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) and
                        not any(word in text.lower() for word in ['gift', 'route', 'scratch', 'attack', 'defense', 'special', 'speed', 'points', 'serebii', 'pokédex', 'net']) and
                        any(char.isalpha() for char in text) and
                        text[0].isalpha() and  # Must start with a letter
                        not text.endswith('-')):  # Must not end with dash
                        pokemon_name = text
                        break
        
        pokemon_data['name'] = pokemon_name
        
        # Get Pokémon number from the title or header
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            if '#' in title_text:
                number_start = title_text.find('#') + 1
                number_end = title_text.find(' ', number_start)
                if number_end == -1:
                    number_end = title_text.find('-', number_start)
                if number_end != -1:
                    pokemon_data['number'] = title_text[number_start:number_end]
        
        # Get types - specifically target Table 2, Row 1, Cell 12 (the actual type column)
        types = []
        tables = soup.find_all('table', class_='dextable')
        if len(tables) >= 2:  # Make sure we have at least 2 tables
            main_table = tables[1]  # Table 2 (index 1)
            rows = main_table.find_all('tr')
            if len(rows) >= 2:  # Make sure we have at least 2 rows (header + data)
                data_row = rows[1]  # Row 1 (index 1) - the data row
                cells = data_row.find_all('td')
                if len(cells) >= 12:  # Make sure we have at least 12 cells
                    type_cell = cells[11]  # 12th column (index 11) - the actual Type column
                    type_images = type_cell.find_all('img', src=lambda x: x and '/pokedex-bw/type/' in x and x.endswith('.gif'))
                    for type_img in type_images:
                        src = type_img.get('src', '')
                        type_name = src.split('/')[-1].replace('.gif', '').title()
                        if type_name not in types:
                            types.append(type_name)
        pokemon_data['types'] = types
        
        # Get other names in different languages
        other_names = {}
        other_name_cells = soup.find_all('td', class_='fooinfo')
        for cell in other_name_cells:
            text = cell.get_text(strip=True)
            if 'Japan:' in text and 'French:' in text and 'German:' in text and 'Korean:' in text:
                # This cell contains all language names
                # Parse Japan first (split into romanized and Japanese)
                if 'Japan:' in text:
                    japan_start = text.find('Japan:') + 6
                    japan_end = text.find('French:')
                    japan_text = text[japan_start:japan_end].strip()
                    
                    # Create nested Japan structure
                    other_names["Japan"] = {}
                    
                    # Find the transition from romanized to Japanese characters
                    for i, char in enumerate(japan_text):
                        if ord(char) > 127:  # Non-ASCII character (likely Japanese)
                            romanized = japan_text[:i].strip()
                            japanese = japan_text[i:].strip()
                            other_names["Japan"]["0"] = romanized
                            other_names["Japan"]["1"] = japanese
                            break
                    else:
                        # If no Japanese characters found, just use the whole text
                        other_names["Japan"]["0"] = japan_text
                        other_names["Japan"]["1"] = ""
                
                # Parse French
                if 'French:' in text:
                    french_start = text.find('French:') + 7
                    french_end = text.find('German:')
                    french_text = text[french_start:french_end].strip()
                    other_names['French'] = french_text
                
                # Parse German
                if 'German:' in text:
                    german_start = text.find('German:') + 7
                    german_end = text.find('Korean:')
                    german_text = text[german_start:german_end].strip()
                    other_names['German'] = german_text
                
                # Parse Korean
                if 'Korean:' in text:
                    korean_start = text.find('Korean:') + 7
                    korean_text = text[korean_start:].strip()
                    other_names['Korean'] = korean_text
                
                break  # Found the cell with all other names, stop looking
        pokemon_data['other_names'] = other_names
        
        # Get classification
        classification_cell = soup.find('td', class_='fooinfo', string=lambda text: text and 'Pokémon' in text)
        if classification_cell:
            pokemon_data['classification'] = classification_cell.get_text(strip=True)
        
        # Get height and weight - use regex to properly split the text
        height_weight_cells = soup.find_all('td', class_='fooinfo')
        height_imperial = ""
        height_metric = ""
        weight_imperial = ""
        weight_metric = ""
        
        for cell in height_weight_cells:
            text = cell.get_text(strip=True)
            if "'" in text and '"' in text and 'm' in text:  # Combined height like "2'04"0.7m"
                # Use regex to find the imperial part (ends with ")
                imperial_match = re.search(r"(\d+'?\d*\"?)", text)
                if imperial_match:
                    height_imperial = imperial_match.group(1)
                    # Get the metric part (everything after the imperial part)
                    metric_start = text.find(height_imperial) + len(height_imperial)
                    height_metric = text[metric_start:].strip()
            elif 'lbs' in text and 'kg' in text:  # Combined weight like "15.2lbs6.9kg"
                # Use regex to find the imperial part (ends with lbs)
                imperial_match = re.search(r"(\d+\.?\d*lbs)", text)
                if imperial_match:
                    weight_imperial = imperial_match.group(1)
                    # Get the metric part (everything after the imperial part)
                    metric_start = text.find(weight_imperial) + len(weight_imperial)
                    weight_metric = text[metric_start:].strip()
        
        pokemon_data['height'] = {
            'imperial': height_imperial,
            'metric': height_metric
        }
        pokemon_data['weight'] = {
            'imperial': weight_imperial,
            'metric': weight_metric
        }
        
        # Get base stats and max stats
        base_stats = {}
        max_stats_lv50 = {}
        max_stats_lv100 = {}
        
        # Look for the stats table
        for table in tables:
            header = table.find('td', class_='fooevo')
            if header and 'Stats' in header.get_text():
                # This is the stats table
                rows = table.find_all('tr')
                for i, row in enumerate(rows):
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        # Look for the row with "Base Stats - Total:"
                        first_cell = cells[0].get_text(strip=True)
                        if 'Base Stats - Total:' in first_cell:
                            # This is the base stats row (Row 3 in the structure)
                            # Extract the BST value from "Base Stats - Total: 253"
                            bst_match = re.search(r'Base Stats - Total:\s*(\d+)', first_cell)
                            if bst_match:
                                base_stats['bst'] = bst_match.group(1)
                            
                            # The first cell contains "Base Stats - Total: 253", actual stats start from cell 1
                            if len(cells) >= 6:  # Need 6 cells: [Base Stats text, HP, Attack, Defense, Special, Speed]
                                base_stats['HP'] = cells[1].get_text(strip=True)
                                base_stats['Attack'] = cells[2].get_text(strip=True)
                                base_stats['Defense'] = cells[3].get_text(strip=True)
                                base_stats['Special'] = cells[4].get_text(strip=True)
                                base_stats['Speed'] = cells[5].get_text(strip=True)
                        
                        # Look for the row with "Max Stats" and "Lv. 50"
                        elif 'Max Stats' in first_cell and len(cells) >= 5:
                            # This is the Lv. 50 max stats row (Row 4 in the structure)
                            max_stats_lv50['HP'] = cells[2].get_text(strip=True)
                            max_stats_lv50['Attack'] = cells[3].get_text(strip=True)
                            max_stats_lv50['Defense'] = cells[4].get_text(strip=True)
                            max_stats_lv50['Special'] = cells[5].get_text(strip=True)
                            max_stats_lv50['Speed'] = cells[6].get_text(strip=True)
                        
                        # Look for the row with "Lv. 100"
                        elif 'Lv. 100' in first_cell and len(cells) >= 5:
                            # This is the Lv. 100 max stats row (Row 5 in the structure)
                            max_stats_lv100['HP'] = cells[1].get_text(strip=True)
                            max_stats_lv100['Attack'] = cells[2].get_text(strip=True)
                            max_stats_lv100['Defense'] = cells[3].get_text(strip=True)
                            max_stats_lv100['Special'] = cells[4].get_text(strip=True)
                            max_stats_lv100['Speed'] = cells[5].get_text(strip=True)
                
                break  # Found the stats table, stop looking
        
        # Create the larger stats object
        stats = {
            "base_stats": base_stats,
            "max_stats": {
                "lv_50": max_stats_lv50,
                "lv_100": max_stats_lv100
            }
        }
        
        pokemon_data['stats'] = stats
        
        # Get capture rate
        capture_rate = ""
        capture_cells = soup.find_all('td', class_='fooinfo')
        for cell in capture_cells:
            text = cell.get_text(strip=True)
            if text.isdigit() and len(text) <= 3:  # Capture rate is usually 1-3 digits
                capture_rate = text
                break
        pokemon_data['capture_rate'] = capture_rate
        
        # Get experience growth and effort values earned - search in page text
        experience_growth = {}
        effort_values = {}
        
        # Search the entire page text for these values
        page_text = soup.get_text()
        
        # Look for experience growth - try different patterns
        exp_patterns = [
            r'([\d,]+)\s+Points\s+([A-Za-z\s]+)',  # "1,059,860 Points Medium Slow"
            r'([\d,]+)\s+Points([A-Za-z\s]+)',     # "1,059,860 PointsMedium Slow"
        ]
        
        for pattern in exp_patterns:
            exp_match = re.search(pattern, page_text)
            if exp_match:
                experience_growth['points'] = exp_match.group(1)
                experience_growth['rate'] = exp_match.group(2).strip()
                break
        
        # Look for effort values - try different patterns
        ev_patterns = [
            (r'(\d+)\s+Hit Points', 'HP'),
            (r'(\d+)\s+Attack', 'Attack'),
            (r'(\d+)\s+Defense', 'Defense'),
            (r'(\d+)\s+Special', 'Special'),
            (r'(\d+)\s+Speed', 'Speed')
        ]
        
        for pattern, stat in ev_patterns:
            ev_match = re.search(pattern, page_text)
            if ev_match:
                effort_values[stat] = ev_match.group(1)
        
        # If we still don't have experience growth, try a broader search
        if not experience_growth:
            # Look for any text containing "Points" and a growth rate
            exp_broad = re.search(r'([\d,]+)\s*Points.*?(Medium Slow|Medium Fast|Fast|Slow)', page_text)
            if exp_broad:
                experience_growth['points'] = exp_broad.group(1)
                experience_growth['rate'] = exp_broad.group(2)
        
        # Fix effort values parsing - look for the specific pattern in the text
        # The text format is like "45 Hit Points49 Attack49 Defense 65 Special45 Speed"
        ev_text_match = re.search(r'(\d+)\s+Hit Points(\d+)\s+Attack(\d+)\s+Defense\s+(\d+)\s+Special(\d+)\s+Speed', page_text)
        if ev_text_match:
            effort_values['HP'] = ev_text_match.group(1)
            effort_values['Attack'] = ev_text_match.group(2)
            effort_values['Defense'] = ev_text_match.group(3)
            effort_values['Special'] = ev_text_match.group(4)
            effort_values['Speed'] = ev_text_match.group(5)
        
        pokemon_data['experience_growth'] = experience_growth
        pokemon_data['effort_values'] = effort_values
        
        # Get damage taken (type effectiveness)
        damage_taken = {}
        # Look for the damage table by searching for "Damage Taken" header
        for table in tables:
            header = table.find('td', class_='foo')
            if header and 'Damage Taken' in header.get_text():
                # This is the damage table
                rows = table.find_all('tr')
                if len(rows) >= 3:  # Header + type row + effectiveness row
                    # Row 1: Header (Damage Taken)
                    # Row 2: Type images
                    # Row 3: Effectiveness values
                    
                    type_row = rows[1]
                    effectiveness_row = rows[2]
                    
                    # Get type names from images in the type row
                    type_cells = type_row.find_all('td', class_='footype')
                    effectiveness_cells = effectiveness_row.find_all('td', class_='footype')
                    
                    # Match types with their effectiveness values
                    for i, type_cell in enumerate(type_cells):
                        if i < len(effectiveness_cells):
                            # Extract type name from image source
                            type_img = type_cell.find('img')
                            if type_img:
                                src = type_img.get('src', '')
                                # Extract type name from path like /games/type/grass2.gif
                                type_match = re.search(r'/games/type/(\w+)2\.gif', src)
                                if type_match:
                                    type_name = type_match.group(1).title()
                                    
                                    # Get corresponding effectiveness value
                                    effectiveness_cell = effectiveness_cells[i]
                                    effectiveness_text = effectiveness_cell.get_text(strip=True)
                                    
                                    # Extract the multiplier (e.g., *1, *2, *0.5, *0.25)
                                    if effectiveness_text.startswith('*'):
                                        multiplier = effectiveness_text[1:]  # Remove the * symbol
                                        damage_taken[type_name] = multiplier
                break
        
        pokemon_data['damage_taken'] = damage_taken
        
        # Get locations
        locations = []
        location_tables = soup.find_all('table', class_='dextable')
        for table in location_tables:
            header = table.find('td', class_='fooevo')
            if header and 'Locations' in header.get_text():
                # This is the locations table
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Handle different row structures
                        if len(cells) == 2:
                            # Standard 2-cell row: [game, place]
                            game = cells[0].get_text(strip=True)
                            place = cells[1].get_text(strip=True)
                            if game and place and game != 'Game' and place != 'Location':
                                locations.append({
                                    "game": game,
                                    "place": place
                                })
                        elif len(cells) == 3:
                            # Special 3-cell row: [game1, game2, place]
                            # This handles cases like "Green (Jp.)" + "Blue (Intl.)" = "Starter Pokémon"
                            game1 = cells[0].get_text(strip=True)
                            game2 = cells[1].get_text(strip=True)
                            place = cells[2].get_text(strip=True)
                            if game1 and game2 and place and place != 'Location':
                                # Combine the two games with "/"
                                combined_game = f"{game1}/{game2}"
                                locations.append({
                                    "game": combined_game,
                                    "place": place
                                })
        
        pokemon_data['locations'] = locations
        
        # Get evolutionary chain
        evos = []
        seen_evos = set()  # Track unique evolutions to avoid duplicates
        for table in tables:
            header = table.find('td', class_='fooevo')
            if header and 'Evolutionary Chain' in header.get_text():
                # This is the evolution table
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Look for evolution data
                        for i, cell in enumerate(cells):
                            # Check for evolution icons (level requirements)
                            evo_icons = cell.find_all('img', src=lambda x: x and 'evoicon/l' in x and x.endswith('.png'))
                            if evo_icons:
                                for icon in evo_icons:
                                    src = icon.get('src', '')
                                    # Extract level from path like /pokedex-xy/evoicon/l16.png
                                    level_match = re.search(r'/l(\d+)\.png$', src)
                                    if level_match:
                                        level = level_match.group(1)
                                        
                                        # Look for the next Pokémon in the evolution chain
                                        # The evolution icons are usually followed by Pokémon sprites
                                        next_mon_cell = None
                                        if i + 1 < len(cells):
                                            next_mon_cell = cells[i + 1]
                                        elif i + 1 < len(cells) - 1:
                                            next_mon_cell = cells[i + 2]
                                        
                                        if next_mon_cell:
                                            # Look for Pokémon sprite images
                                            mon_sprites = next_mon_cell.find_all('img', src=lambda x: x and '/pokearth/sprites/' in x and x.endswith('.png'))
                                            if mon_sprites:
                                                for sprite in mon_sprites:
                                                    sprite_src = sprite.get('src', '')
                                                    # Extract Pokémon number from path like /pokearth/sprites/yellow/002.png
                                                    mon_match = re.search(r'/(\d+)\.png$', sprite_src)
                                                    if mon_match:
                                                        mon_number = mon_match.group(1)
                                                        # Only add if it's not the current Pokémon (001) and we haven't seen this evolution
                                                        if mon_number != "001":
                                                            evo_key = f"{level}-{mon_number}"
                                                            if evo_key not in seen_evos:
                                                                seen_evos.add(evo_key)
                                                                evos.append({
                                                                    "level": level,
                                                                    "mon": mon_number
                                                                })
                break
        
        pokemon_data['evos'] = evos
        
        # Get moves - separate into learnset and TM moves with detailed information
        learnset_moves = []
        tm_moves = []
        
        # Find all move tables
        move_tables = soup.find_all('table', class_='dextable')
        for table in move_tables:
            # Check if this is a moves table by looking for the header
            header = table.find('td', class_='fooevo')
            if header:
                header_text = header.get_text(strip=True)
                if 'Generation I Level Up' in header_text:
                    # This is the learnset table
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 7:  # Need enough cells for all move details
                            level = cells[0].get_text(strip=True)
                            move_name = cells[1].get_text(strip=True)
                            
                            # Extract move type from image in the type cell
                            move_type = ""
                            type_cell = cells[2]
                            type_img = type_cell.find('img', src=lambda x: x and '/pokedex-bw/type/' in x and x.endswith('.gif'))
                            if type_img:
                                src = type_img.get('src', '')
                                move_type = src.split('/')[-1].replace('.gif', '').title()
                            
                            power = cells[3].get_text(strip=True)
                            accuracy = cells[4].get_text(strip=True)
                            pp = cells[5].get_text(strip=True)
                            effect = cells[6].get_text(strip=True) if len(cells) > 6 else ""
                            
                            if level and move_name and level != 'Level' and move_name != 'Attack Name':
                                # Look for move description in the next row or nearby
                                description = ""
                                next_row = row.find_next_sibling('tr')
                                if next_row:
                                    desc_cells = next_row.find_all('td')
                                    if desc_cells and len(desc_cells) > 0:
                                        description = desc_cells[0].get_text(strip=True)
                                
                                learnset_moves.append({
                                    'level': level,
                                    'name': move_name,
                                    'type': move_type,
                                    'power': power,
                                    'accuracy': accuracy,
                                    'pp': pp,
                                    'effect': effect,
                                    'description': description
                                })
                elif 'TM & HM Attacks' in header_text:
                    # This is the TM moves table
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 7:  # Need enough cells for all move details
                            tm_number = cells[0].get_text(strip=True)
                            move_name = cells[1].get_text(strip=True)
                            
                            # Extract move type from image in the type cell
                            move_type = ""
                            type_cell = cells[2]
                            type_img = type_cell.find('img', src=lambda x: x and '/pokedex-bw/type/' in x and x.endswith('.gif'))
                            if type_img:
                                src = type_img.get('src', '')
                                move_type = src.split('/')[-1].replace('.gif', '').title()
                            
                            power = cells[3].get_text(strip=True)
                            accuracy = cells[4].get_text(strip=True)
                            pp = cells[5].get_text(strip=True)
                            effect = cells[6].get_text(strip=True) if len(cells) > 6 else ""
                            
                            if tm_number and move_name and tm_number != 'TM/HM #' and move_name != 'Attack Name':
                                # Look for move description in the next row or nearby
                                description = ""
                                next_row = row.find_next_sibling('tr')
                                if next_row:
                                    desc_cells = next_row.find_all('td')
                                    if desc_cells and len(desc_cells) > 0:
                                        description = desc_cells[0].get_text(strip=True)
                                
                                tm_moves.append({
                                    'tm_number': tm_number,
                                    'name': move_name,
                                    'type': move_type,
                                    'power': power,
                                    'accuracy': accuracy,
                                    'pp': pp,
                                    'effect': effect,
                                    'description': description
                                })
        
        pokemon_data['moves'] = {
            'learnset': learnset_moves,
            'tm_moves': tm_moves
        }
        
        # Download sprite images to local sprites folder
        pokemon_number = pokemon_data.get('number', '001')
        base_url = "https://www.serebii.net"
        
        # Create the proper folder structure: data/[pokemon_number]/sprites/
        data_folder = "data"
        pokemon_folder = os.path.join(data_folder, pokemon_number)
        sprites_folder = os.path.join(pokemon_folder, "sprites")
        os.makedirs(sprites_folder, exist_ok=True)
        
        # Download the 6 sprite images with proper naming
        sprite_urls = [
            ("/pokearth/sprites/green/" + pokemon_number + ".png", f"g{pokemon_number}.png"),
            ("/pokearth/sprites/rb/" + pokemon_number + ".png", f"rb{pokemon_number}.png"),
            ("/pokearth/sprites/yellow/" + pokemon_number + ".png", f"y{pokemon_number}.png"),
            ("/pokearth/sprites/green/" + pokemon_number + "-g.png", f"g{pokemon_number}-g.png"),
            ("/pokearth/sprites/rb/" + pokemon_number + "-g.png", f"rb{pokemon_number}-g.png"),
            ("/pokearth/sprites/yellow/" + pokemon_number + "-g.png", f"y{pokemon_number}-g.png")
        ]
        
        for sprite_url, filename in sprite_urls:
            full_url = urljoin(base_url, sprite_url)
            local_path = os.path.join(sprites_folder, filename)
            try:
                download_image(full_url, local_path)
            except Exception as e:
                print(f"Warning: Could not download {filename}: {e}")
                # Continue with other images even if one fails
        
        # Save individual Pokémon JSON
        save_to_json(pokemon_data, f"{pokemon_number}.json")
        
        return pokemon_data
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_gen1_pokedex():
    """
    Scrape all 151 Pokémon from Gen 1 Pokédex
    """
    base_url = "https://www.serebii.net/pokedex/{:03d}.shtml"
    all_pokemon = []
    
    print("Starting to scrape Gen 1 Pokédex...")
    
    for i in range(1, 152):  # 1 to 151
        url = base_url.format(i)
        print(f"Scraping #{i:03d}...")
        
        pokemon_data = scrape_pokemon_page(url)
        if pokemon_data:
            all_pokemon.append(pokemon_data)
            print(f"✓ {pokemon_data.get('name', f'#{i}')}")
        else:
            print(f"✗ Failed to scrape #{i}")
        
        # Be respectful - add a small delay between requests
        time.sleep(1)
    
    return all_pokemon

def save_to_json(data, filename):
    """
    Save scraped data to a JSON file in the proper folder structure
    """
    # If data is a list, save to the main data folder
    if isinstance(data, list):
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filepath}")
    else:
        # If data is a single Pokémon, save to data/[pokemon_number]/[pokemon_number].json
        pokemon_number = data.get('number', '001')
        pokemon_folder = os.path.join("data", pokemon_number)
        os.makedirs(pokemon_folder, exist_ok=True)
        filepath = os.path.join(pokemon_folder, f"{pokemon_number}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filepath}")

def main():
    """
    Main function to run the scraper
    """
    print("Pokémon Gen 1 Pokédex Scraper")
    print("=" * 40)
    
    # Scrape all Pokémon
    pokemon_list = scrape_gen1_pokedex()
    
    if pokemon_list:
        print(f"\nSuccessfully scraped {len(pokemon_list)} Pokémon!")
        
        # Save to JSON file in data folder
        save_to_json(pokemon_list, 'gen1_pokedex.json')
        
        # Show a sample of the first Pokémon
        if pokemon_list:
            print("\nSample data for first Pokémon:")
            print(json.dumps(pokemon_list[0], indent=2))
    else:
        print("No Pokémon data was scraped.")

if __name__ == "__main__":
    main()
