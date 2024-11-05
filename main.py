import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import re
import requests
import google.generativeai as genai

# Load the API keys from key.txt
with open("key.txt", "r") as file:
    keys = file.readlines()
    GENAI_API_KEY = keys[0].strip()      # First line for Gemini API key
    SEARCH_API_KEY = keys[1].strip()     # Second line for Google Search API key
    SEARCH_ENGINE_ID = keys[2].strip()   # Third line for Search Engine ID

# Configure Gemini with the loaded API key
genai.configure(api_key=GENAI_API_KEY)

# Web search function to find item dimensions
def search_item_dimensions(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": SEARCH_API_KEY,
        "cx": SEARCH_ENGINE_ID
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if "items" in data:
        snippet = data["items"][0]["snippet"]
        return snippet
    
    return None

# Function to parse dimensions and weight using Gemini with interactive refinement
def parse_with_gemini(item_name, snippet):
    prompt = (
        f"The following text provides some information about a {item_name}:\n\n"
        f"{snippet}\n\n"
        "Please provide only the estimated length, width, height (in cm), and weight (in kg) of the item, "
        "based on typical values if exact details aren't available. Do not provide any additional explanations."
    )

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    return extract_dimensions_and_weight(response.text)

# Helper function to extract dimensions and weight from Gemini's response text
def extract_dimensions_and_weight(text):
    dimensions = "Unknown"
    weight = "Unknown"

    # Use regular expressions to find dimensions and weight
    length_match = re.search(r"length:\s*([\d\.]+)\s*cm", text, re.IGNORECASE)
    width_match = re.search(r"width:\s*([\d\.]+)\s*cm", text, re.IGNORECASE)
    height_match = re.search(r"height:\s*([\d\.]+)\s*cm", text, re.IGNORECASE)
    weight_match = re.search(r"weight:\s*([\d\.]+)\s*kg", text, re.IGNORECASE)
    
    if length_match and width_match and height_match:
        dimensions = (
            float(length_match.group(1)),
            float(width_match.group(1)),
            float(height_match.group(1))
        )
    if weight_match:
        weight = float(weight_match.group(1))
    
    return dimensions, weight

# Popup for confirming item dimensions
def confirm_item_dimensions(item_name, dimensions, weight, parent):
    while True:
        prompt_text = (
            f"Estimated dimensions and weight for {item_name}:\n"
            f"Length: {dimensions[0]} cm\n"
            f"Width: {dimensions[1]} cm\n"
            f"Height: {dimensions[2]} cm\n"
            f"Weight: {weight} kg\n\n"
            "Is this information correct? If not, provide additional details or type 'no' to try again."
        )
        
        response = simpledialog.askstring("Confirm Dimensions", prompt_text, parent=parent)

        if response is None:
            return None, None  # Cancel action
        elif response.lower() == "yes":
            return dimensions, weight
        elif response.lower() != "no":
            # User provided additional information; refine search with new info
            snippet = search_item_dimensions(response)
            if snippet:
                dimensions, weight = parse_with_gemini(item_name, snippet)
            else:
                messagebox.showinfo("Search Result", "No details found online with the additional info provided.")
        else:
            return None, None  # Default exit if the user can't confirm

# Main GUI Application
class SuitcaseOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pack-It: The Optimal Suitcase Organizer")
        self.root.geometry("700x600")
        self.root.minsize(700, 600)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(7, weight=1)

        # Add padding around widgets for a cleaner look
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Suitcase Dimensions Input
        tk.Label(frame, text="Enter Suitcase Dimensions (in cm):", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        self.length_entry = self.create_label_entry(frame, "Length:")
        self.width_entry = self.create_label_entry(frame, "Width:")
        self.height_entry = self.create_label_entry(frame, "Height:")

        # Item Input Section
        tk.Label(frame, text="Enter Item Details:", font=("Arial", 12, "bold")).pack(pady=(20, 10))
        self.item_name_entry = self.create_label_entry(frame, "Item Name:", entry_width=30)
        self.items = []

        # Buttons to Add Item and Confirm
        button_frame = tk.Frame(frame)
        button_frame.pack(pady=15)
        tk.Button(button_frame, text="Add Item", command=self.add_item, width=15).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(button_frame, text="Calculate and Organize", command=self.calculate_and_organize, width=20).pack(side=tk.LEFT)

        # Scrollable Text Box for AI Output
        self.output_box = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Arial", 10))
        self.output_box.pack(pady=(20, 0), fill=tk.BOTH, expand=True)

    def create_label_entry(self, parent, label_text, entry_width=10):
        """Creates a label and entry field, returning the entry widget."""
        frame = tk.Frame(parent)
        frame.pack(pady=5, fill=tk.X)
        tk.Label(frame, text=label_text, font=("Arial", 10)).pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=entry_width)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        return entry

    def add_item(self):
        item_name = self.item_name_entry.get()
        if not item_name:
            messagebox.showwarning("Input Error", "Please enter an item name.")
            return
        
        # Search dimensions online and get AI confirmation
        snippet = search_item_dimensions(item_name + " average dimensions")
        while True:
            if snippet:
                dimensions, weight = parse_with_gemini(item_name, snippet)
                if dimensions != "Unknown" and weight != "Unknown":
                    # Confirm dimensions in a popup
                    dimensions, weight = confirm_item_dimensions(item_name, dimensions, weight, self.root)
                    if dimensions and weight:
                        self.items.append({"name": item_name, "dimensions": dimensions, "weight": weight})
                        self.output_box.insert(tk.END, f"Added {item_name} - Dimensions: {dimensions} cm, Weight: {weight} kg\n")
                        break
                    else:
                        self.output_box.insert(tk.END, f"No confirmed dimensions for {item_name}. Skipping.\n")
                        break
            else:
                # Handle case where no snippet is returned and prompt user for additional details
                self.output_box.insert(tk.END, f"No dimensions found for '{item_name}' online. Asking for additional info.\n")
                response = simpledialog.askstring("Additional Information", f"No dimensions found for '{item_name}'.\nPlease provide additional details (e.g., brand, size, or type):", parent=self.root)
                if response:
                    snippet = search_item_dimensions(response)
                    item_name = response  # Update the item name for more accurate feedback
                else:
                    self.output_box.insert(tk.END, f"Skipping '{item_name}' due to lack of information.\n")
                    break

        # Clear the entry field after processing
        self.item_name_entry.delete(0, tk.END)

    def calculate_and_organize(self):
        # Suitcase dimensions
        try:
            length = float(self.length_entry.get())
            width = float(self.width_entry.get())
            height = float(self.height_entry.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter valid suitcase dimensions.")
            return
        
        suitcase = {
            "length": length,
            "width": width,
            "height": height,
            "items": self.items
        }

        organization_plan = self.ask_gemini_for_organization_and_calculation(suitcase)
        self.output_box.insert(tk.END, "\n--- Suitcase Organization Plan ---\n")
        self.output_box.insert(tk.END, organization_plan)

    def ask_gemini_for_organization_and_calculation(self, suitcase):
        items_list = "\n".join(
            f"{item['name']}: {item['dimensions'][0]} x {item['dimensions'][1]} x {item['dimensions'][2]} cm, Weight: {item['weight']} kg"
            for item in suitcase['items'] if item['dimensions'] != "Unknown"
        )
        
        prompt = (
            f"I have a suitcase with dimensions {suitcase['length']} cm x {suitcase['width']} cm x {suitcase['height']} cm. "
            "Here is a list of items with their dimensions and weights:\n"
            f"{items_list}\n\n"
            "Please calculate the total space taken, remaining space, and total weight of these items. "
            "Provide concise folding instructions (if applicable) and placement suggestions without any additional explanations."
        )
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        return response.text

# Running the Application
if __name__ == "__main__":
    root = tk.Tk()
    app = SuitcaseOrganizerApp(root)
    root.mainloop()
