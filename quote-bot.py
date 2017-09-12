import discord
import random
import sqlite3
import atexit

client = discord.Client()
conn = sqlite3.connect('/home/pi/DiscordQuoteBot/quotes.db')
quotebook = None


def on_exit():
    conn.commit()
    conn.close()
atexit.register(on_exit)


@client.event
async def on_ready():
    global quotebook
    print('Connected!')
    print('Username: ' + client.user.name)
    print('ID: ' + client.user.id)
    server = client.get_server('196064250559463434')
    for c in server.channels:
        if c.id == '277199318245703681':
            quotebook = c
            break


@client.event
async def on_message(message):
    if message.content.startswith('!quote '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        conn.execute('INSERT OR IGNORE INTO Users (ID, NAME) VALUES ({}, \'{}\')'.format(message.author.id, message.author.name))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE!="BLOCKED") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            qid = ''.join(str(random.randrange(0, 10)) for _ in range(8))
            if message.server is not None:
                conn.execute('INSERT INTO Quotes (QID, TIMESTAMP, SENDER, QUOTE) VALUES ("{}", date("now"), {}, {})'.format(str(qid), message.author.id, "'" + message.content[7:].replace("'", "''") + "'"))
                conn.commit()
                await client.delete_message(message)
                await client.send_message(message.channel, '{}, your quote was submitted! (ID: {})'.format(message.author.name, qid))
                for user in conn.execute('SELECT ID FROM Users WHERE TYPE="ADMIN"'):
                    await client.send_message(message.server.get_member(str(user[0])), 'Quote {} submitted by {} ({}):\n```{}```\nReply with `!accept {}`, `!reject {}`, or `!revise {} [revision]`.'.format(qid, message.author.name, message.author.id, message.content[7:], qid, qid, qid))
                print('> Submitted the quote "{}" with ID {}.'.format(message.content[7:], qid))
            else:
                print('> ERROR: User tried to submit a quote while not in a server.')
                await client.send_message(message.channel, 'Sorry, you cannot use that command here.')
        else:
            print('> ERROR: User does not have permission to use command "!quote".'.format(message.author.name, message.author.id))
            await client.delete_message(message)
            await client.send_message(message.channel, 'Sorry {}, you are blocked from submitting quotes.'.format(message.author.name))
    elif message.content.startswith('!accept '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE="ADMIN") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            qid = message.content[8:]
            if conn.execute('SELECT EXISTS(SELECT 1 FROM Quotes WHERE (QID="{}") LIMIT 1)'.format(qid)).fetchall()[0][0] == 1:
                quote = conn.execute('SELECT * FROM Quotes WHERE QID="{}"'.format(qid)).fetchall()[0]
                if quote[5] == 0:
                    conn.execute('UPDATE Quotes SET ADMIN="{}", STATUS="1" WHERE QID="{}"'.format(message.author.id, qid))
                    conn.commit()
                    await client.send_message(quotebook, quote[4])
                    await client.send_message(message.channel, 'Quote {} successfully accepted.'.format(qid))
                    print('> Submitted the quote with ID {} and posted to #quotebook.'.format(qid))
                elif quote[5] == 1:
                    print('> ERROR: Quote has already been accepted by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6]))
                    await client.send_message(message.channel, 'ERROR: Quote has already been accepted by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6]))
                else:
                    print('> ERROR: Quote has been rejected by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6], qid, qid))
                    await client.send_message(message.channel, 'ERROR: Quote has been rejected by {} ({}). To override, use `!unlock {}` and `!accept {}`.'.format(quotebook.server.get_member(str(quote[6])).name, quote[6], qid, qid))
            else:
                print('> ERROR: Invalid Quote ID: {}.'.format(qid))
                await client.send_message(message.channel, 'ERROR: Invalid Quote ID: {}.'.format(qid))
        else:
            print('> ERROR: User does not have permission to use command "!accept".')
            await client.send_message(message.channel, 'ERROR: You do not have permission to use this command.')
    elif message.content.startswith('!reject '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE="ADMIN") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            qid = message.content[8:]
            if conn.execute('SELECT EXISTS(SELECT 1 FROM Quotes WHERE (QID="{}") LIMIT 1)'.format(qid)).fetchall()[0][0] == 1:
                quote = conn.execute('SELECT * FROM Quotes WHERE QID="{}"'.format(qid)).fetchall()[0]
                if quote[5] == 0:
                    conn.execute('UPDATE Quotes SET ADMIN="{}", STATUS="2" WHERE QID="{}"'.format(message.author.id, qid))
                    conn.commit()
                    await client.send_message(message.channel, 'Quote {} successfully rejected.'.format(qid))
                    print('> Rejected the quote with ID {}.'.format(qid))
                elif quote[5] == 1:
                    print('> ERROR: Quote has been accepted by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6]))
                    await client.send_message(message.channel, 'ERROR: Quote has been accepted by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6]))
                else:
                    print('> ERROR: Quote has already been rejected by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6]))
                    await client.send_message(message.channel, 'ERROR: Quote has already been rejected by {} ({}).'.format(quotebook.server.get_member(str(quote[6])).name, quote[6]))
            else:
                print('> ERROR: Invalid Quote ID: {}.'.format(qid))
                await client.send_message(message.channel, 'ERROR: Invalid Quote ID: {}.'.format(qid))
        else:
            print('> ERROR: User does not have permission to use command "!reject".')
            await client.send_message(message.channel, 'ERROR: You do not have permission to use this command.')
    elif message.content.startswith('!unlock '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE="ADMIN") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            qid = message.content[8:]
            if conn.execute('SELECT EXISTS(SELECT 1 FROM Quotes WHERE (QID="{}") LIMIT 1)'.format(qid)).fetchall()[0][0] == 1:
                quote = conn.execute('SELECT * FROM Quotes WHERE QID="{}"'.format(qid)).fetchall()[0]
                if quote[5] != 0:
                    conn.execute('UPDATE Quotes SET ADMIN=NULL, STATUS="0" WHERE QID="{}"'.format(qid))
                    conn.commit()
                    await client.send_message(message.channel, 'Quote {} successfully unlocked.'.format(qid))
                    print('> Quote {} successfully unlocked.'.format(qid))
                else:
                    print('> ERROR: Quote is already unlocked.')
                    await client.send_message(message.channel, 'ERROR: Quote is already unlocked.')
            else:
                print('> ERROR: Invalid Quote ID: {}.'.format(qid))
                await client.send_message(message.channel, 'ERROR: Invalid Quote ID: {}.'.format(qid))
        else:
            print('> ERROR: User does not have permission to use command "!unlock".')
            await client.send_message(message.channel, 'ERROR: You do not have permission to use this command.')
    elif message.content.startswith('!revise '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE="ADMIN") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            qid = message.content[8:16]
            if conn.execute('SELECT EXISTS(SELECT 1 FROM Quotes WHERE (QID="{}") LIMIT 1)'.format(qid)).fetchall()[0][0] == 1:
                conn.execute('UPDATE Quotes SET QUOTE={} WHERE QID="{}"'.format("'" + message.content[17:].replace("'", "''") + "'", qid))
                conn.commit()
                await client.send_message(message.channel, 'Quote {} successfully revised.'.format(qid))
                print('Quote {} successfully revised to "{}".'.format(qid, message.content[17:].replace('\n', '\\n')))
            else:
                print('> ERROR: Invalid Quote ID: {}.'.format(qid))
                await client.send_message(message.channel, 'ERROR: Invalid Quote ID: {}.'.format(qid))
        else:
            print('> ERROR: User does not have permission to use command "!revise".')
            await client.send_message(message.channel, 'ERROR: You do not have permission to use this command.')
    elif message.content.startswith('!qblock '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE="ADMIN") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            for member in message.mentions:
                conn.execute('INSERT OR IGNORE INTO Users (ID, NAME) VALUES ({}, \'{}\')'.format(member.id, member.name))
                conn.execute('UPDATE Users SET TYPE="BLOCKED" WHERE ID="{}"'.format(member.id))
                conn.commit()
                print('> User {} ({}) is now blocked from submitting quotes.'.format(member.name, member.id))
        else:
            print('> ERROR: User does not have permission to use command "!qblock".')
            await client.send_message(message.channel, 'ERROR: You do not have permission to use this command.')
    elif message.content.startswith('!qunblock '):
        print('{} ({}) sent command "{}".'.format(message.author.name, message.author.id, message.content.replace('\n', '\\n')))
        if conn.execute('SELECT EXISTS(SELECT 1 FROM Users WHERE (ID="{}" AND TYPE="ADMIN") LIMIT 1)'.format(message.author.id)).fetchall()[0][0] == 1:
            for member in message.mentions:
                conn.execute('INSERT OR IGNORE INTO Users (ID, NAME) VALUES ({}, \'{}\')'.format(member.id, member.name))
                conn.execute('UPDATE Users SET TYPE="MEMBER" WHERE ID="{}"'.format(member.id))
                conn.commit()
                print('> User {} ({}) is now unblocked from submitting quotes.'.format(member.name, member.id))
        else:
            print('> ERROR: User does not have permission to use command "!qunblock".')
            await client.send_message(message.channel, 'ERROR: You do not have permission to use this command.')
#
client.run('MzUzMDQwMDgwMDE0ODAyOTY1.DIp7uw.0i4McdeiBXUOqNTUPj1xuLvbuuM')
