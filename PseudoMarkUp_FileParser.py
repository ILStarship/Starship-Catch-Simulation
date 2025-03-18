from enum import Enum
import pygame

spacing = 5 # px
            # X spacing between elements

class ElementType(Enum):
    
    # --- Headers ---
    HEADER1 = 0
    HEADER2 = 1
    HEADER3 = 3
    HEADER4 = 4

    # --- Link to Image ---
    IMAGE = 5

    # --- Body --- 
    BODY = 6

    # --- Comment ---
    COMMENT = 7

TextTypeSize = {ElementType.HEADER1: 50, ElementType.HEADER2: 45, ElementType.HEADER3: 40, ElementType.HEADER4: 35, ElementType.BODY: 25} # Font size of different element types

class PseudoMarkUpParser():
    def __init__(self, total_scroll_min, total_scroll_max, scroll_limit = True):
        self.text_attributes = [] # Stores text, type of text, size of text, and x origin of text is as a string in a dictionary. A list then stores the ditionaries of each line.
        self.total_scroll_offset = 0 # Stores absolute value of scroll offset

        self.total_scroll_min = total_scroll_min
        self.total_scroll_max = total_scroll_max

        self.scroll_limit = scroll_limit

    def get_element_type(self, text: str):
        """Returns type of text, eg: header, image, body"""

        if "[HEADER1]" in text:
            return ElementType.HEADER1
        
        elif "[HEADER2]" in text:
            return ElementType.HEADER2
        
        elif "[HEADER3]" in text:
            return ElementType.HEADER3

        elif "[HEADER4]" in text:
            return ElementType.HEADER4

        elif "[IMAGE]" in text:
            return ElementType.IMAGE
        
        elif "[COMMENT]" in text:
            return ElementType.COMMENT

        elif "[BODY]" in text:
            return ElementType.BODY
        
        else:
            return ElementType.BODY

    def remove_type(self, text: list):
        """Removes type, eg: [BODY] from string"""

        # --- Header ---
        text = text.replace("[HEADER1]", "")
        text = text.replace("[HEADER2]", "")
        text = text.replace("[HEADER3]", "")
        text = text.replace("[HEADER4]", "")

        # --- Image ---
        text = text.replace("[IMAGE]", "")

        # --- Body ---
        text = text.replace("[BODY]", "")

        return text

    def convert_file(self, source_file):

        element_y_origin = 10 # Y origin of each element

        with open(source_file) as instruct_file: # Open source file
            for line in instruct_file: # Interate through all lines in file

                # Write text content, type, size, and y origin into dictionary
                element_type = self.get_element_type(line)
                if element_type != ElementType.COMMENT:
                    # Line isn't a comment
                    self.text_attributes.append({"Text": self.remove_type(line).rstrip(), "Y Origin": element_y_origin, 
                                                "Type": element_type, "Size": TextTypeSize[element_type] if element_type != ElementType.IMAGE else None})

                    if self.text_attributes[len(self.text_attributes)-1]["Type"] != ElementType.IMAGE:
                        # Line isn't an image
                        element_y_origin += TextTypeSize[element_type] + spacing # Update Y-origin of next element
                    else:
                        # Line is an image
                        # Update Y origin of next element by the height of the image
                        try:
                            element_y_origin += pygame.image.load(self.text_attributes[len(self.text_attributes)-1]["Text"]).get_height() + 10
                        except FileNotFoundError:
                            print("Displaying Image Failed! File Counldn't be found!")
                            element_y_origin += 35
    
    def display_content(self, screen: pygame.display.set_mode, scroll_offset: int=0):
        """Displays content from self.text_attributes. Includes scrolling to move text up and down"""

        self.total_scroll_offset += scroll_offset # Update (absolute) scroll offset
        if self.scroll_limit:
            # Scroll limit enabled
            self.total_scroll_offset = max(min(self.total_scroll_offset, self.total_scroll_max), self.total_scroll_min)
        else:
            # Scroll limit disabled likely to check limits -> print total_scroll
            print(self.total_scroll_offset)

        for element in self.text_attributes: # For every element in text_attributes
            if element["Type"] != ElementType.IMAGE:
                # Type isn't an image
                #font = pygame.font.SysFont(None, element["Size"])
                font = pygame.font.SysFont("Agency FB", element["Size"])
                txt_img = font.render(element["Text"], True, (0,0,0))
                screen.blit(txt_img, (10, element["Y Origin"]+self.total_scroll_offset))
            else:
                try:
                    img = pygame.image.load(element["Text"])
                    screen.blit(img, (10, element["Y Origin"]+self.total_scroll_offset))
                except FileNotFoundError:
                    print("Displaying Image Failed! File Counldn't be found!")
                    font = pygame.font.SysFont(None, 25)
                    txt_img = font.render("[?UNABLE TO DISPLAY IMAGE]", True, (255,0,0))
                    screen.blit(txt_img, (10, element["Y Origin"]+self.total_scroll_offset))
    
    def print_attributes(self):
        """Display attributes of self.text_attributes"""
        print(self.text_attributes)
