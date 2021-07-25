# Hand detection applied to Tetris

This app shows gesture detection powerful possibilities using Tetris game as an example.Techniks applied here can be applied to many gesture recognition problems.

usage:
python main.py

See config.txt for configuration options. 


# Game

https://user-images.githubusercontent.com/65562440/126897474-3cc366ad-4bcc-4357-add5-0b5888a517f3.mp4



# How it works?

## Hand detection with Mediapipe
Mediapipe offers great library for hand landmarks recognition. 

https://user-images.githubusercontent.com/65562440/126897676-444513e3-22ee-4a64-9e44-920ca7279e21.mp4


## Rotation detection
Based on detected landmarks gestures and moves can be calculated. Rotation is detected based on angle between wrist and middle finger. If the angle is above some treshold the gesture can be detected. It is important to correct the angle thresholds based on current hand possition, as there arise natural bend as the user moves the hand to the one side of the screen. Additionally there is default angle thresholds correction implemented in one side, as it can be easier to bend the hand to one of the sides depending one the user handedness. Additional angle boundary (green on the video) is necessary to enable rotation move again after detection. The angle settings can be configured in config.txt

https://user-images.githubusercontent.com/65562440/126897647-3924ca33-4633-4e23-9ac6-983caa51b7de.mp4

## Move Detection
We move the block as the user moves hand to the side of the screen. The move is detected if hand is beyond some threshold distance from hand natural position. The hand natural position is calculated dynamically as it would be impossible for the user to keep the hand always in the middle of the screen. This enables to detect the move only on dynamic and intended hand moves. The more the hand goes to the side the bigger the velocity value and the faster the block moves.   

https://user-images.githubusercontent.com/65562440/126897662-1c11719b-4969-41ae-bb16-699dfc79a378.mp4




