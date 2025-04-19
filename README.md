# Land Starship in the Chopsticks!

>[!IMPORTANT]
># Location of Files
>Code, images, audio, and all other files of the game must be placed in the same folder. An example of how to place the files could be found in the directory ![File Location Example](https://github.com/ILStarship/Starship-Catch-Simulation/tree/Release---V2.2.1/File%20Location%20Example)).

>[!IMPORTANT]
>In lines `471-480` of StarshipCatchSimMain.py, a `match` statement is used. However, this is only supported in Python 3.10 and onwards. If your Python version doesn't support `match`, change the code from
>```
>match level:
>    case 1:
>        difficulty_level = Difficulty.EASY
>        print("[EASY]")
>    case 2:
>        difficulty_level = Difficulty.MEDIUM
>        print("[MEDIUM]")
>    case 3:
>        difficulty_level = Difficulty.HARD
>        print("[HARD]")
>```
>to
>```
>    if level == 1:
>        difficulty_level = Difficulty.EASY
>        print("[EASY]")
>    elif level == 2:
>        difficulty_level = Difficulty.MEDIUM
>        print("[MEDIUM]")
>    elif level == 3:
>        difficulty_level = Difficulty.HARD
>        print("[HARD]")
>```
