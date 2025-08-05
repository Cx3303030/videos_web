import re

class ChmodConversion():
    
    def __init__(self) -> None:
        pass
    
    def int_to_perm(self,x:int):
        chmod_map_int={
            0:"---",
            1:"--x",
            2:"-w-",
            3:"-wx",
            4:"r--",
            5:"r-x",
            6:"rw-",
            7:"rwx"
        }
        o = x%10
        g = int((x/10)%10)
        u = int((x/100)%10)
        l = [u,g,o]
        s=""
        for i in l:
            if i in chmod_map_int.keys():
                    s+=chmod_map_int[i]
            else:
                return ("Incorrect value")
        return s 
    
    def perm_to_int(self, x:str):
        regex=re.compile("((---)|(--x)|(-w-)|(-wx)|(r--)|(r-x)|(rw-)|(rwx)){3}")
        chmod_map_perm={
            "---":0,
            "--x":1,
            "-w-":2,
            "-wx":3,
            "r--":4,
            "r-x":5,
            "rw-":6,
            "rwx":7
        }
        if len(x)==0:
            return("Empty string")
        if len(x)%9!=0 and len(x)%6!=0 and len(x)%3!=0:
            return("Incorrect length")
        u = x[:3]
        g = x[3:6]
        o = x[6:9]
        l =[u,g,o]
        s=""
        error = []
        for i in l:
            if i in chmod_map_perm.keys():
                s+=f'{chmod_map_perm[i]}'
            else:
                if i !="":
                    if re.match(regex,i) is None:
                        error.append(f"{i}: Incorrect format (has to be in this format - rwx)")
        if len(s)<3:
            error_string =""
            for i in error:
                error_string+= f'{i}\n'
            return error_string
        else:
            return s       
