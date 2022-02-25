import discord, math, json, requests, random, os
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv

load_dotenv()


intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix='.', intents=intents)

def CheckIfCounter(counter, team, allocated, participants):
    if counter in allocated:
        counter += 1
        team, allocated = CheckIfCounter(counter, team, allocated, participants)
    else:
        team.append(participants[counter])
        allocated.append(counter)
    return team, allocated

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.command(name='assign_roles', pass_context=True)
@commands.has_role("Admin")
async def assignRoles(ctx):
    members = ctx.guild.members
    participants = ctx.guild.members
    for i in members:
        if 'Minecraft Player' not in [role.name for role in i.roles[1:]]:
            participants.remove(i)
    weights = []
    for i in participants:
        with open('usernames.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        uuid = data.get(str(i.id))
        response = requests.get('https://api.hypixel.net/player'
                                '?key='+str(os.getenv('HYPIXEL_TOKEN'))+'&uuid='+str(uuid))
        content = response.json()
        swKDR = int(content["player"]["stats"]["SkyWars"]["kills"])/int(content["player"]["stats"]["SkyWars"]["deaths"])
        bwKDR = int(content["player"]["stats"]["Bedwars"]["final_kills_bedwars"])/int(content["player"]
                                                                                      ["stats"]["Bedwars"]
                                                                                      ["final_deaths_bedwars"])
        duelsWL = int(content["player"]["stats"]["Duels"]["wins"])/int(content["player"]["stats"]["Duels"]["losses"])
        weight = swKDR + bwKDR + duelsWL
        weights.append(weight)
    teamOneWeight = 0
    teamTwoWeight = 0
    team1 = []
    team2 = []
    team = 1
    allocated = []
    while True:
        teamWeights = []
        totalWeight = 0
        if team == 1:
            difference = teamOneWeight - teamTwoWeight
        else:
            difference = teamTwoWeight - teamOneWeight

        for i in weights:
            if difference == 0:
                weighting = int(math.ceil(i * 1000))
            elif difference > 0:
                weighting = int(math.ceil(i * 1000 / i / i * abs(difference)))
            elif difference < 0:
                weighting = int(math.ceil(i * 1000 * i / abs(difference)))
            totalWeight += weighting
            teamWeights.append(weighting)
        choice = random.randint(0, totalWeight)
        counter = 0
        weighted = 0
        for i in teamWeights:
            if choice <= int(i) + weighted:
                if team == 1:
                    team1, allocated = CheckIfCounter(counter, team1, allocated, participants)
                    teamOneWeight += weights[counter]
                else:
                    team2, allocated = CheckIfCounter(counter, team2, allocated, participants)
                    teamTwoWeight += weights[counter]
                del weights[counter]
                break
            else:
                weighted += i
                counter += 1
        if weights == []:
            break

        if team == 1:
            team = 2
        elif team == 2:
            team = 1
    teamOnePlayers = ""
    teamTwoPlayers = ""
    for i in team1:
        role_id = 945847378391466036
        role = get(ctx.guild.roles, id=role_id)
        await i.add_roles(role, reason = None, atomic = True)
        teamOnePlayers += str(i.name) + ", "
    for i in team2:
        role_id = 945847458385240176
        role = get(ctx.guild.roles, id=role_id)
        await i.add_roles(role, reason = None, atomic = True)
        teamTwoPlayers += str(i.name) + ", "
    teamOnePlayers = teamOnePlayers.rstrip(", ")
    teamTwoPlayers = teamTwoPlayers.rstrip(", ")
    toReplace = teamOnePlayers.rfind(",")
    teamOnePlayers = teamOnePlayers[:toReplace] + " and " + teamOnePlayers[toReplace + 1:]
    toReplace = teamTwoPlayers.rfind(",")
    teamTwoPlayers = teamTwoPlayers[:toReplace] + " and " + teamTwoPlayers[toReplace + 1:]
    await ctx.send('On the <@&945847378391466036> there are ' + teamOnePlayers + ".")
    await ctx.send('On the <@&945847458385240176> there are ' + teamTwoPlayers + ".")


@client.command(name='username')
async def setUsername(ctx, arg):
    larg = arg.lower()
    response = requests.get('https://api.mojang.com/users/profiles/minecraft/' + larg)
    if str(response) != '<Response [200]>':
        await ctx.send('UUID not found. Response Code: '+str(response))
    else:
        content = response.json()
        uuid = content['id']
        with open('usernames.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        f.close()
        if str(ctx.author.id) in data:
            data.pop(str(ctx.author.id))
        data.update({ctx.author.id: uuid})
        with open('usernames.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        f.close()
        await ctx.send('<@'+str(ctx.author.id)+'>\'s username has been updated to '+content['name']+'.')




#@client.event
#async def on_message(message):
#    if message.author == client.user:
#        return
#
#    if message.content.startswith('$hello'):
#        await message.channel.send('Hello!')
#
#    # if message.content.startswith('!assign_roles'):
#    #     await message.channel.send('<@573087122345426954>')

client.run(os.getenv('DISCORD_TOKEN'))