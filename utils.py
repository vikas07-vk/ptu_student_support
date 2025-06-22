import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

class PTUUtils:
    def __init__(self):
        self.base_url = "https://ptu.ac.in"
        self.pdf_directory = "static/pdfs"
        
        # Create PDF directory if it doesn't exist
        if not os.path.exists(self.pdf_directory):
            os.makedirs(self.pdf_directory)
        
        # Dictionary mapping course types to their PDF files
        self.pdf_files = {
            "fee_structure": {
                "btech": "static/pdfs/btech_fees.pdf",
                "mtech": "static/pdfs/mtech_fees.pdf",
                "mba": "static/pdfs/mba_fees.pdf"
            },
            "timetable": {
                "btech": "static/pdfs/btech_timetable.pdf",
                "mtech": "static/pdfs/mtech_timetable.pdf",
                "mba": "static/pdfs/mba_timetable.pdf"
            },
            "syllabus": {
                "btech": "static/pdfs/btech_syllabus.pdf",
                "mtech": "static/pdfs/mtech_syllabus.pdf",
                "mba": "static/pdfs/mba_syllabus.pdf"
            }
        }

    def get_pdf_path(self, doc_type, course):
        """Get the path to a specific PDF file."""
        try:
            return self.pdf_files[doc_type.lower()][course.lower()]
        except KeyError:
            return None

    def get_notices(self):
        try:
            # URL for PTU notices
            url = "https://ptu.ac.in/notices"
            
            # Send GET request
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find notice elements (adjust selectors based on actual website structure)
            notice_elements = soup.select('.notice-item')  # Update this selector
            
            notices = []
            for element in notice_elements[:10]:  # Get latest 10 notices
                try:
                    title = element.select_one('.notice-title').text.strip()
                    date = element.select_one('.notice-date').text.strip()
                    link = element.select_one('a')['href']
                    
                    if not link.startswith('http'):
                        link = self.base_url + link
                    
                    notices.append({
                        'title': title,
                        'date': date,
                        'link': link
                    })
                except Exception as e:
                    print(f"Error parsing notice element: {e}")
                    continue
            
            return notices
            
        except Exception as e:
            print(f"Error fetching notices: {e}")
            # Return some sample notices if scraping fails
            return [
                {
                    'title': 'Notice regarding End Semester Examination May-June 2024',
                    'date': '15-04-2024',
                    'link': 'https://ptu.ac.in/notices/end-sem-exam-2024'
                },
                {
                    'title': 'Academic Calendar for Even Semester 2024',
                    'date': '10-04-2024',
                    'link': 'https://ptu.ac.in/notices/academic-calendar-2024'
                },
                {
                    'title': 'Important Notice for Final Year Students',
                    'date': '05-04-2024',
                    'link': 'https://ptu.ac.in/notices/final-year-notice'
                }
            ]

    def format_notice_response(self, notices):
        if not notices:
            return "No recent notices found. Please check back later."
        
        response = "Here are the recent notices from PTU:\n\n"
        for i, notice in enumerate(notices, 1):
            response += f"{i}. {notice['title']}\n"
            response += f"   Date: {notice['date']}\n"
            response += f"   Link: {notice['link']}\n\n"
        
        return response

    def get_document_response(self, doc_type, course):
        try:
            # Map document types to their respective PDF files
            doc_mapping = {
                'fee_structure': {
                    'btech': 'btech_fees.pdf',
                    'mtech': 'mtech_fees.pdf',
                    'mba': 'mba_fees.pdf'
                },
                'timetable': {
                    'btech': 'btech_timetable.pdf',
                    'mtech': 'mtech_timetable.pdf',
                    'mba': 'mba_timetable.pdf'
                },
                'syllabus': {
                    'btech': 'btech_syllabus.pdf',
                    'mtech': 'mtech_syllabus.pdf',
                    'mba': 'mba_syllabus.pdf'
                }
            }
            
            if doc_type not in doc_mapping or course not in doc_mapping[doc_type]:
                return f"Sorry, the requested document ({doc_type} for {course}) is not available."
            
            filename = doc_mapping[doc_type][course]
            file_path = os.path.join(self.pdf_directory, filename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                return f"The requested document ({filename}) is not available at the moment."
            
            # Return download link
            download_url = f"/download/{doc_type}/{course}"
            return f"You can download the {doc_type} for {course.upper()} here: {download_url}"
            
        except Exception as e:
            print(f"Error getting document response: {e}")
            return "Sorry, there was an error processing your document request."

    def get_pdf_path(self, doc_type, course):
        """Get the path to a specific PDF file."""
        try:
            return self.pdf_files[doc_type.lower()][course.lower()]
        except KeyError:
            return None

    def get_notices(self, limit=10):
        """Scrape notices from PTU website."""
        try:
            response = requests.get(f"{self.base_url}/notices")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                notices = []
                
                # Adjust these selectors based on PTU website structure
                notice_elements = soup.select('.notice-board li')  # Update selector as per actual website
                
                for element in notice_elements[:limit]:
                    notice = {
                        'title': element.get_text(strip=True),
                        'link': element.find('a')['href'] if element.find('a') else None,
                        'date': element.find('span', class_='date').text if element.find('span', class_='date') else None
                    }
                    notices.append(notice)
                
                return notices
            return []
        except Exception as e:
            print(f"Error scraping notices: {str(e)}")
            return []

    def format_notice_response(self, notices):
        """Format notices into a readable response."""
        if not notices:
            return "No recent notices available at the moment."
        
        response = "Recent Notices from PTU:\n\n"
        for idx, notice in enumerate(notices, 1):
            response += f"{idx}. {notice['title']}\n"
            if notice['date']:
                response += f"   Date: {notice['date']}\n"
            if notice['link']:
                response += f"   Link: {self.base_url}{notice['link']}\n"
            response += "\n"
        
        return response

    def get_document_response(self, doc_type, course):
        """Generate response for document requests."""
        pdf_path = self.get_pdf_path(doc_type, course)
        
        if not pdf_path:
            return f"Sorry, the {doc_type} for {course} is not available at the moment."
        
        if not os.path.exists(pdf_path):
            return f"The {doc_type} file for {course} is currently being updated. Please try again later."
        
        download_url = f"/download/{doc_type}/{course}"
        response = f"You can download the {course.upper()} {doc_type} using this link:\n"
        response += f"Download Link: {download_url}\n\n"
        
        return response 