class Solution:
  
    def find_number(self, target:int, numberList:list[int] = []):
        
        least = 0 
        high = len(numberList) - 1
        while least <= high:
            mid = (high + least)//2

            if numberList[mid] == target:
                return 'Yes it is here'

            elif numberList[mid] < target:
                least = mid + 1

            else:
                high = mid - 1
        return 'target value not found' 
