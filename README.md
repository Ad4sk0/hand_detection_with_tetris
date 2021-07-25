# Gesture detection applied to Tetris

This app presents powerful possibilities of gesture detection using Tetris game as an example.Technics applied here can be used for solving many gesture recognition problems.

Run:<br>
python main.py

See config.txt for configuration options. 

# Game

### Control options
There are three moves possible in Tetris:
- **Move block left or right** - 
Just move hand intensively to the left or right - the further is the move the faster the block goes to this side
- **Move block down** - 
Works similar as left or down but this time move your hand to the bottom of the screen
- **Rotate block** -
Turn your hand to the left or right - the block will rotate one time to the same side
  
https://user-images.githubusercontent.com/65562440/126897474-3cc366ad-4bcc-4357-add5-0b5888a517f3.mp4

# How it works?

### Hand detection with Mediapipe
Mediapipe offers a great library for hand landmarks recognition. 

https://user-images.githubusercontent.com/65562440/126897676-444513e3-22ee-4a64-9e44-920ca7279e21.mp4


### Rotation detection
Hand motion and gestures are determined based on detected landmarks. The rotation gesture is detected based on the angle 
between wrist, middle fingertip and {wrist x, 0} point. If the angle difference goes beyond a certain threshold (red line in the video below), 
the gesture is detected.

Additional angle threshold (green in the video below) is necessary to enable rotation move again after detection. 
After rotation detection the hand has to go back to its natural position (between green lines) in order to enable rotation again. 

It is important to dynamically adjust the angle threshold values depending on current hand position.
The shift in the position of one wrist across X axis may cause an involuntary movements in other parts of the hand and 
naturally bend the fingers to the side which changes the default angle between wrist and middle finger. For this reason,
the more the hand goes in one side on X axis the more the thresholds are being bent in this direction. 

Depending on the handedness of the person it is easier to rotate hand in either left or right direction. That's why there 
is additionally angle correction constant added, which cause to move the rotation thresholds more to the one of the sides.

The angle settings can be configured in config.txt

https://user-images.githubusercontent.com/65562440/126897647-3924ca33-4633-4e23-9ac6-983caa51b7de.mp4

### Move Detection
The Tetris block is moved as the user moves their hand to the border of the screen. 

Similar to rotation detection the move is detected if the hand is beyond some threshold (red circle in the video below) 
from "default" hand position, count in pixel distance this time. 

The "default" hand position is calculated dynamically, so that the user does not have to move back their hand to the 
centre of the screen after each gesture, which strongly reduces unintentional detections.

This enables the detection mechanism to be triggered by dynamic and intended hand moves.

The further and more dynamically the hand goes to the border of the screen the bigger the velocity value, hence the block moves faster.   

https://user-images.githubusercontent.com/65562440/126897662-1c11719b-4969-41ae-bb16-699dfc79a378.mp4




