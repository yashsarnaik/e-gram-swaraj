import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd

def scrape_egramswaraj_table():
    """
    Scrape the eGramSwaraj state summary report table and save to CSV
    """
    try:
        # Send request to the webpage
        url = 'https://egramswaraj.gov.in/FileRedirect.jsp?FD=SummaryReport2025-2026/27&name=27.html'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the main table
        table = soup.find('table')
        
        if not table:
            print("No table found on the webpage")
            return
        
        # Extract all rows
        rows = table.find_all('tr')
        
        if not rows:
            print("No rows found in the table")
            return
        
        # Process the table data
        table_data = []
        
        for row_idx, row in enumerate(rows):
            # Get all cells (both th and td)
            cells = row.find_all(['th', 'td'])
            row_data = []
            
            for cell in cells:
                # Handle colspan and rowspan attributes
                colspan = int(cell.get('colspan', 1))
                rowspan = int(cell.get('rowspan', 1))
                
                # Get cell text and clean it
                cell_text = cell.get_text(strip=True)
                
                # Add the cell data
                row_data.append(cell_text)
                
                # Add empty cells for colspan > 1
                for _ in range(colspan - 1):
                    row_data.append('')
            
            table_data.append(row_data)
        
        # Find the maximum number of columns to ensure consistent row lengths
        max_cols = max(len(row) for row in table_data) if table_data else 0
        
        # Pad rows to have the same number of columns
        for row in table_data:
            while len(row) < max_cols:
                row.append('')
        
        # Save to CSV using pandas for better handling
        df = pd.DataFrame(table_data)
        
        # Save to CSV
        csv_filename = 'egramswaraj_state_summary.csv'
        df.to_csv(csv_filename, index=False, header=False, encoding='utf-8')
        
        print(f"Table successfully saved to {csv_filename}")
        print(f"Table dimensions: {len(table_data)} rows x {max_cols} columns")
        
        # Display first few rows for verification
        print("\nFirst 5 rows of the scraped data:")
        for i, row in enumerate(table_data[:5]):
            print(f"Row {i+1}: {row[:5]}...")  # Show first 5 columns
        
        return df
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def scrape_with_manual_structure():
    """
    Alternative approach with more detailed structure preservation
    """
    try:
        url = 'https://egramswaraj.gov.in/FileRedirect.jsp?FD=SummaryReport2025-2026/27&name=27.html'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("No table found")
            return None
        
        # Extract table with structure preservation
        all_rows = []
        
        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            row_data = []
            
            for cell in cells:
                # Get text content
                text = cell.get_text(separator=' ', strip=True)
                
                # Handle merged cells
                colspan = int(cell.get('colspan', 1))
                rowspan = int(cell.get('rowspan', 1))
                
                # Add cell data
                row_data.append(text)
                
                # Add empty cells for colspan
                for _ in range(colspan - 1):
                    row_data.append('')
            
            all_rows.append(row_data)
        
        # Ensure all rows have the same length
        if all_rows:
            max_length = max(len(row) for row in all_rows)
            for row in all_rows:
                while len(row) < max_length:
                    row.append('')
        
        # Save to CSV
        filename = 'egramswaraj_detailed.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(all_rows)
        
        print(f"Detailed table saved to {filename}")
        print(f"Dimensions: {len(all_rows)} rows x {max_length} columns")
        
        return all_rows
        
    except Exception as e:
        print(f"Error in detailed scraping: {e}")
        return None

if __name__ == "__main__":
    print("Scraping eGramSwaraj State Summary Report...")
    print("-" * 50)
    
    # Try the main scraping function
    df = scrape_egramswaraj_table()
    
    print("\n" + "="*50)
    print("Trying alternative detailed approach...")
    
    # Try alternative approach
    detailed_data = scrape_with_manual_structure()
    
    print("\nScraping completed!")