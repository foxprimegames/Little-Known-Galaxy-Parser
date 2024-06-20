Collection of Parser Items for the Little-Known Galaxy wiki found at: https://lkg.wiki.gg/ <br>
Putting these into output files, so we can do a compare between patches, and only update pages that need it.

dialogueParser.py -- <br>
  Looks at a file folder: Input/TextAsset (should be replaced with each patch)<br>
  Parses the "English_NPCNAME.txt" files into a format used by the wiki. WIKI: Each region should be a section on the NPC's /Dialogue page. Emotes to text should be associated correctly.<br>
  Puts each file in file folder: Output/Dialogues<br>
