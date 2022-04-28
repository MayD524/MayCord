"""
    Author: May Draskovics
    Date: 2/26/2022
    Description: This is the room security module.
"""

from difflib import SequenceMatcher

class roomSecurity:
    def __init__(self, profanityList:str="./database/prof_words.txt",
                    fillWith:str="*") -> None:
        self.profanityList = profanityList
        self.fillWith = fillWith
        
        with open(self.profanityList, "r") as f:
            self.profanity = f.read().splitlines()
            
        for i in range(len(self.profanity)):
            self.profanity[i] = self.profanity[i].lower().strip()
            
            
    def censor(self, text:str) -> tuple[str, bool]:
        isProf = False
        text = text.lower()
        for word in self.profanity:
            if word in text and self.checkSimularity(word, text, 0.7):
                text = text.replace(word, self.fillWith * len(word))
                isProf = True
        return (text, isProf)
    
    def censorMessage(self, text:str) -> tuple[str, bool]:
        isProf = False
        if " " not in text:
            return self.censor(text)

        txt = text.split(" ")
        
        for i in range(len(txt)):
            if txt[i] == "":
                continue
            
            txt[i], tProf = self.censor(txt[i])
            if tProf:
                isProf = True
                
        return (" ".join(txt), isProf)
    
    @staticmethod
    def checkSimularity(string1:str, string2:str, tooSimilar:float=0.56) -> bool:
        if len(string1) != len(string2): return False
        elif string1 == string2: return True
        else: return SequenceMatcher(None, string1, string2).ratio() > tooSimilar