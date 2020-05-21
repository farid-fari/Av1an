from commands import GetAudio, SplitFile, PasteFiles, All
import sys


input = sys.argv[1]
fo = open('Makefile', 'w')
splits = [5, 15, 30]

print(All().makeCommand(), file=fo)
print(GetAudio(input).makeCommand(), file=fo)
print(SplitFile(input, splits).makeCommand(), file=fo)
print(PasteFiles(splits).makeCommand(), file=fo)

fo.close()
