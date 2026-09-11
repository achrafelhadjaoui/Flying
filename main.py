import sys
from parsing import Parser



def main() -> None:
    """the starting of the project where we read from terminal commands
    """
    
    if (len(sys.argv) != 2) :
        print("enter path of file")
        exit(3)
    file = ""
    try:
        file = Parser()
        file.file_check(sys.argv[1])
        file.clean_content()
        file.first_line_check()
    except Exception as e:
        print(e)
        exit(3)
    #print(file.content)
    
    
        
        
        
        
    
main()
     