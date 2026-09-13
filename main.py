import sys
from controller import validate_data
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
        file.first_line_check()
        file.zone_check()
        file.connection_check()
        validate_data(file.data)
        #print(file.data["zones"][1])
        print(file.data)
    except Exception as e:
        print(str(e))
        exit(3)
    #print(file.content)
    
    
        
        
        
        
    
main()
     