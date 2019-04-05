# Import db from app
from app import db
# Import module models
from app.mod_game.models import Game, Player, Score, Cricket, Round, Throw
# cycle and islice for nextPlayer
from itertools import cycle, islice

# Method definitions
def clear_db():
    db.session.query(Game).delete()
    db.session.query(Score).delete()
    db.session.query(Cricket).delete()
    db.session.query(Throw).delete()
    db.session.query(Round).delete()

    playingPlayersObject = Player.query.filter_by(game_id=1).all()
    for player in playingPlayersObject:
        player.game_id = None
        player.active = 0

    db.session.commit()

def getActivePlayer():
    activePlayerObject = Player.query.filter_by(active=True).first()
    return activePlayerObject

def getPlayingPlayers():
    playingPlayersObject = Player.query.filter_by(game_id=1).all()
    listOfPlayingPlayers = []
    # Fill in active Players list
    for player in playingPlayersObject:
        listOfPlayingPlayers.append(player.name)

    return listOfPlayingPlayers

def getPlayingPlayersObjects():
    playingPlayersObject = Player.query.filter_by(game_id=1).all()
    return playingPlayersObject

def getPlayingPlayersID():
    playingPlayersObject = Player.query.filter_by(game_id=1).all()
    listOfPlayingPlayersID = []
    # Fill in active Players list
    for player in playingPlayersObject:
        listOfPlayingPlayersID.append(player.id)

    return listOfPlayingPlayersID

def getScore(playerID):
    score = Score.query.filter_by(player_id=playerID).first()
    return score.score

def checkIfOngoingGame():
    ongoing = False
    if Player.query.filter_by(active=True).first():
        ongoing = True

    return ongoing

def checkIfOngoingRound(activePlayer):
    # Check if there is a ongoing round associated with player
    ongoing = None
    nextPlayerNeeded = None
    rnd = Round.query.filter_by(player_id=activePlayer.id, ongoing=1).first()

    if not rnd:
        ongoing = False
    else:
        if rnd.throwcount < 3:
            ongoing = True
        else:
            ongoing = False

    return ongoing

def scoreX01(hit,mod):
    # Some modeling for the resulting words on cli/browser
    if hit == 25:
        hitword = "Bullseye"
    elif hit == 0:
        hitword = "Out of board"
    else:
        hitword = hit
    if mod == 1:
        modifier = ""
    elif mod == 2:
        modifier = "Double"
    elif mod == 3:
        modifier = "Triple"
    # calculate points to be substracted from score
    points = hit * mod
    # check if there is a game going on
    if checkIfOngoingGame():
        # set active player
        activePlayer = Player.query.filter_by(active=True).first()
        # TODO Here startIn and exitOut should be set to a variable
        #
        # TODO Here also startIn should be checked like:
        # If PlayerScore is inital score then check if startIn is Double/Master
        # Check if modifier fits and then either create first round or game.nextPlayerNeeded = 1
        #
        # Check if there is a ongoing round associated, if not create a new one
        if not checkIfOngoingRound(activePlayer):
            rnd = Round(player_id=activePlayer.id,ongoing=True,throwcount=0)
            db.session.add(rnd)
            db.session.commit()
        else:
            # Set round object
            rnd = Round.query.filter_by(player_id=activePlayer.id, ongoing=1).first()

        # get Game object
        game = Game.query.first()
        # Check if ongoing round is over
        if rnd.throwcount == 3:
            game.nextPlayerNeeded = True
        else:
            # set throwcount and old score
            throwcount = rnd.throwcount
            playerScore = Score.query.filter_by(player_id=activePlayer.id).first()
            # check if bust
            if playerScore.score - points < 0:
                game.nextPlayerNeeded = True
                throwcount += 1
                rnd.throwcount = throwcount
                #rnd.throwcount = 3
                playerScore.score = playerScore.parkScore
                db.session.commit()
                return "Bust\n"
            # check if won
            elif playerScore.score - points == 0:
                # TODO Here might be the best place to implement statistics function
                # TODO Also implement exitOut here
                #
                game.won = True
                activePlayer.active = False
                throwcount += 1
                rnd.throwcount = throwcount
                playerScore.score = 0
                db.session.commit()
                return "Game has been won\n"
            # define new score, increase throwcount, commit to db
            else:
                newScore = playerScore.score - points
                throwcount += 1
                playerScore.score = newScore
                rnd.throwcount = throwcount
                throw = Throw(hit=hit,mod=mod,round_id=rnd.id)
                if throwcount == 3:
                    playerScore.parkScore = newScore
                    game.nextPlayerNeeded = True
                db.session.add(throw)
                db.session.commit()

                result = "Hit is {} {}\n".format(modifier,hitword)
                result += "New score is {}\n".format(newScore)
                return result
    else:
        # Output if no game is running
        return "There is no active game running\n"

def switchNextPlayer():
    # First set active Player round ongoing to 0 and nextPlayerNeeded in Game to 0
    activePlayerObject = getActivePlayer()
    activePlayerObject = Player.query.filter_by(active=True).first()
    activePlayerRound = Round.query.filter_by(player_id=activePlayerObject.id, ongoing=1).first()
    activePlayerRound.ongoing = False
    game = Game.query.first()
    game.nextPlayerNeeded = False
    # Initialize variables to work with
    key = []
    listOfPlayingPlayers = getPlayingPlayers()
    # Find key of active player in list
    for i, x in enumerate(listOfPlayingPlayers):
        if x == str(activePlayerObject):
            positionInListOfActivePlayer = i
    # Fill a list from 0 to x as long as the list of active players
    for x in range (0, len(listOfPlayingPlayers)):
        key.append(x)
    # define cycle over key list
    cyclePlayerKeyInList = cycle(key)
    # start at position of active player in the keyList
    positionKeyAfterActivePlayerKey = islice(cyclePlayerKeyInList, positionInListOfActivePlayer+1, None)
    # Take one step in list and define next player with the resulting key
    nextPlayerKeyInList = next(positionKeyAfterActivePlayerKey)
    nextActivePlayerObject = Player.query.filter_by(name=listOfPlayingPlayers[nextPlayerKeyInList]).first()
    # Commit current active player false and next active player true to database
    activePlayerObject.active = False
    nextActivePlayerObject.active = True
    db.session.commit()
    # Result for command line/Browser to catch when called
    result = ""
    result += "activePlayer = {}\n".format(activePlayerObject)
    result += "listOfPlayingPlayers: {}\n".format(listOfPlayingPlayers)
    result += "nextPlayerKeyInList is {} which is {}\n".format(nextPlayerKeyInList,listOfPlayingPlayers[nextPlayerKeyInList])
    return result