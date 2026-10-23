import argparse
import multiprocessing as mp
import asyncio
from hashlib import sha256
import hashlib
import json
import random
import time
from typing import ClassVar
from urllib.parse import quote
from pathlib import Path
import uuid
import websockets

from src.utils.cooldown import Cooldown

from ..utils.message_logger import MessageLogger, MessageLoggerImpl


pronouns = [
    "I",
    "You",
    "He",
    "She",
    "It",
    "We",
    "They",
    "Someone",
    "Everyone",
    "Nobody",
    "This",
    "That",
    "My",
    "Your",
    "His",
    "Her",
    "Our",
    "Their",
]

# ГЛАГОЛЫ (60+ штук)
verbs = [
    "love",
    "hate",
    "see",
    "want",
    "need",
    "create",
    "build",
    "destroy",
    "fix",
    "break",
    "understand",
    "believe",
    "think",
    "know",
    "learn",
    "teach",
    "explain",
    "ask",
    "answer",
    "run",
    "walk",
    "jump",
    "fly",
    "swim",
    "drive",
    "ride",
    "travel",
    "move",
    "stop",
    "eat",
    "drink",
    "cook",
    "make",
    "prepare",
    "taste",
    "smell",
    "hear",
    "listen",
    "watch",
    "read",
    "write",
    "draw",
    "paint",
    "sing",
    "dance",
    "play",
    "work",
    "study",
    "practice",
    "open",
    "close",
    "start",
    "finish",
    "continue",
    "change",
    "improve",
    "develop",
    "grow",
    "die",
]

# ПРИЛАГАТЕЛЬНЫЕ (50+ штук)
adjectives = [
    "good",
    "bad",
    "beautiful",
    "ugly",
    "big",
    "small",
    "huge",
    "tiny",
    "fast",
    "slow",
    "smart",
    "stupid",
    "clever",
    "dumb",
    "interesting",
    "boring",
    "exciting",
    "calm",
    "crazy",
    "normal",
    "happy",
    "sad",
    "angry",
    "calm",
    "excited",
    "tired",
    "sleepy",
    "hungry",
    "thirsty",
    "cold",
    "hot",
    "warm",
    "cool",
    "fresh",
    "old",
    "new",
    "young",
    "ancient",
    "modern",
    "future",
    "simple",
    "complex",
    "easy",
    "hard",
    "dark",
    "light",
    "bright",
    "colorful",
    "empty",
    "full",
]

# СУЩЕСТВИТЕЛЬНЫЕ (60+ штук)
nouns = [
    "world",
    "universe",
    "earth",
    "sky",
    "ocean",
    "mountain",
    "river",
    "forest",
    "desert",
    "city",
    "person",
    "animal",
    "plant",
    "robot",
    "machine",
    "computer",
    "phone",
    "car",
    "house",
    "food",
    "water",
    "fire",
    "air",
    "stone",
    "metal",
    "wood",
    "paper",
    "book",
    "pen",
    "paint",
    "music",
    "song",
    "movie",
    "game",
    "sport",
    "science",
    "math",
    "art",
    "history",
    "language",
    "love",
    "hate",
    "fear",
    "joy",
    "sadness",
    "anger",
    "peace",
    "war",
    "life",
    "death",
    "dream",
    "nightmare",
    "secret",
    "mystery",
    "problem",
    "solution",
    "question",
    "answer",
    "beginning",
    "end",
]

# ДОПОЛНИТЕЛЬНЫЕ КАТЕГОРИИ ДЛЯ РАЗНООБРАЗИЯ
adverbs = [
    "very",
    "really",
    "quite",
    "extremely",
    "absolutely",
    "totally",
    "almost",
    "barely",
    "always",
    "never",
    "sometimes",
    "often",
    "rarely",
    "quickly",
    "slowly",
    "carefully",
    "loudly",
    "quietly",
]

prepositions = [
    "in",
    "on",
    "at",
    "for",
    "with",
    "without",
    "about",
    "around",
    "through",
    "across",
    "during",
    "after",
    "before",
    "under",
    "over",
    "between",
    "among",
]

conjunctions = [
    "and",
    "but",
    "or",
    "so",
    "because",
    "although",
    "however",
    "therefore",
    "meanwhile",
]

question_words = [
    "Why",
    "What",
    "When",
    "Where",
    "Who",
    "Which",
    "How",
    "How much",
    "How many",
]

# НАРЕЧИЯ ВРЕМЕНИ
time_words = [
    "today",
    "tomorrow",
    "yesterday",
    "now",
    "then",
    "soon",
    "later",
    "recently",
    "before",
    "after",
    "finally",
    "suddenly",
]

# СЛОВА ДЛЯ НАЧАЛА ПРЕДЛОЖЕНИЙ
starters = [
    "Well",
    "Actually",
    "Honestly",
    "Surprisingly",
    "Unfortunately",
    "Luckily",
    "Basically",
    "Seriously",
    "Maybe",
    "Perhaps",
    "Anyway",
    "So",
    "Thus",
    "Indeed",
]


def generate_message() -> str:
    id = str(uuid.uuid4())
    body = _generate_message_body()
    return f"{body} [ID={id}]"

def _generate_message_body():

    # 15 различных паттернов для разнообразия
    pattern = random.randint(1, 15)

    if pattern == 1:
        # Pronoun + verb + adjective + noun
        return f"{random.choice(pronouns)} {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)}."

    elif pattern == 2:
        # Pronoun + verb + noun
        return (
            f"{random.choice(pronouns)} {random.choice(verbs)} {random.choice(nouns)}."
        )

    elif pattern == 3:
        # Adjective + noun + verb + adverb
        return f"{random.choice(adjectives)} {random.choice(nouns)} {random.choice(verbs)} {random.choice(adverbs)}."

    elif pattern == 4:
        # Question word + verb + pronoun + preposition + noun?
        return f"{random.choice(question_words)} {random.choice(verbs)} {random.choice(pronouns).lower()} {random.choice(prepositions)} {random.choice(nouns)}?"

    elif pattern == 5:
        # Time word + pronoun + verb + adjective + noun
        return f"{random.choice(time_words)}, {random.choice(pronouns)} {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)}."

    elif pattern == 6:
        # Starter + sentence
        return f"{random.choice(starters)}, {random.choice(pronouns)} {random.choice(verbs)} {random.choice(nouns)} {random.choice(adverbs)}."

    elif pattern == 7:
        # Pronoun + verb + preposition + noun
        return f"{random.choice(pronouns)} {random.choice(verbs)} {random.choice(prepositions)} {random.choice(nouns)}."

    elif pattern == 8:
        # Two clauses with conjunction
        return f"{random.choice(pronouns)} {random.choice(verbs)} {random.choice(nouns)} {random.choice(conjunctions)} {random.choice(pronouns).lower()} {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)}."

    elif pattern == 9:
        # Adverb + verb + pronoun + noun
        return f"{random.choice(adverbs).capitalize()} {random.choice(verbs)} {random.choice(pronouns).lower()} {random.choice(nouns)}."

    elif pattern == 10:
        # Sometimes I like to verb noun
        return f"{random.choice(time_words).capitalize()} {random.choice(pronouns).lower()} {random.choice(['like', 'love', 'hate', 'want', 'need'])} to {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)}."

    elif pattern == 11:
        # It seems + adjective + to + verb + noun
        return f"It seems {random.choice(adjectives)} to {random.choice(verbs)} {random.choice(nouns)} {random.choice(time_words)}."

    elif pattern == 12:
        # There is/are + adjective + noun + preposition + noun
        verb_be = random.choice(["is", "are"])
        return f"There {verb_be} {random.choice(adjectives)} {random.choice(nouns)} {random.choice(prepositions)} the {random.choice(nouns)}."

    elif pattern == 13:
        # Let's + verb + noun + together
        return f"Let's {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)} {random.choice(['together', 'right now', 'soon', 'later'])}!"

    elif pattern == 14:
        # What if + pronoun + verb + noun?
        return f"What if {random.choice(pronouns).lower()} {random.choice(verbs)} {random.choice(nouns)}? That would be {random.choice(adjectives)}!"

    else:
        # Short exclamation or statement
        return f"{random.choice(['Wow', 'Oh', 'Hmm', 'Phew', 'Yikes', 'Awesome', 'Terrible'])}! {random.choice(pronouns)} {random.choice(verbs)} {random.choice(nouns)} {random.choice(adverbs)}."


# === АНГЛИЙСКИЕ ИМЕНА (FIRST NAMES) ===
first_names_male = [
    "James",
    "John",
    "Robert",
    "Michael",
    "William",
    "David",
    "Richard",
    "Joseph",
    "Thomas",
    "Charles",
    "Christopher",
    "Daniel",
    "Matthew",
    "Anthony",
    "Donald",
    "Mark",
    "Paul",
    "Steven",
    "Andrew",
    "Kenneth",
    "Joshua",
    "Kevin",
    "Brian",
    "George",
    "Edward",
    "Ronald",
    "Timothy",
    "Jason",
    "Jeffrey",
    "Ryan",
    "Jacob",
    "Gary",
    "Nicholas",
    "Eric",
    "Jonathan",
    "Stephen",
    "Larry",
    "Justin",
    "Scott",
    "Brandon",
    "Benjamin",
    "Samuel",
    "Gregory",
    "Frank",
    "Alexander",
    "Raymond",
    "Patrick",
    "Jack",
    "Dennis",
    "Jerry",
]

first_names_female = [
    "Mary",
    "Patricia",
    "Jennifer",
    "Linda",
    "Elizabeth",
    "Barbara",
    "Susan",
    "Jessica",
    "Sarah",
    "Karen",
    "Lisa",
    "Nancy",
    "Betty",
    "Margaret",
    "Sandra",
    "Ashley",
    "Kimberly",
    "Emily",
    "Donna",
    "Michelle",
    "Carol",
    "Amanda",
    "Dorothy",
    "Melissa",
    "Deborah",
    "Stephanie",
    "Rebecca",
    "Sharon",
    "Laura",
    "Cynthia",
    "Kathleen",
    "Amy",
    "Shirley",
    "Angela",
    "Helen",
    "Anna",
    "Brenda",
    "Pamela",
    "Nicole",
    "Emma",
    "Samantha",
    "Katherine",
    "Christine",
    "Debra",
    "Rachel",
    "Carolyn",
    "Janet",
    "Catherine",
    "Maria",
    "Heather",
]

first_names_unisex = [
    "Alex",
    "Casey",
    "Jordan",
    "Taylor",
    "Morgan",
    "Riley",
    "Jessie",
    "Jamie",
    "Cameron",
    "Quinn",
    "Avery",
    "Blake",
    "Dakota",
    "Elliott",
    "Harper",
    "Logan",
    "Parker",
    "Reese",
    "Sawyer",
    "Skyler",
]

# ВСЕ ИМЕНА ВМЕСТЕ
all_first_names = first_names_male + first_names_female + first_names_unisex

# === ФАМИЛИИ (LAST NAMES/SURNAMES) ===
last_names = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
    "Carter",
    "Roberts",
    "Phillips",
    "Evans",
    "Turner",
    "Parker",
    "Collins",
    "Edwards",
    "Stewart",
    "Flores",
    "Morris",
    "Murphy",
]

# === ВТОРЫЕ ИМЕНА / ОТЧЕСТВА (MIDDLE NAMES) ===
middle_names = [
    "James",
    "John",
    "Robert",
    "Michael",
    "William",
    "David",
    "Joseph",
    "Thomas",
    "Charles",
    "Edward",
    "Henry",
    "Frank",
    "Raymond",
    "Paul",
    "George",
    "Walter",
    "Arthur",
    "Richard",
    "Louis",
    "Albert",
    "Ann",
    "Marie",
    "Lynn",
    "Lee",
    "Rose",
    "Elizabeth",
    "Grace",
    "Jane",
    "Ruth",
    "Claire",
    "Nicole",
    "Michelle",
    "Renee",
    "Dawn",
    "Marie",
    "Jo",
    "Mae",
    "Sue",
    "Kay",
    "Faye",
    "Alan",
    "Brian",
    "Kevin",
    "Scott",
    "Mark",
    "Steven",
    "Andrew",
    "Daniel",
    "Matthew",
    "Ryan",
    "Alexander",
    "Benjamin",
    "Christopher",
    "Dylan",
    "Ethan",
    "Gabriel",
    "Hunter",
    "Isaiah",
    "Jacob",
    "Liam",
]

# === ПРЕФИКСЫ (SUFFIXES) ===
suffixes = ["Jr.", "Sr.", "II", "III", "IV", "PhD", "MD", "Esq.", "CPA", "Ret."]

# === ФУНКЦИИ ДЛЯ ГЕНЕРАЦИИ ИМЁН ===


def generate_full_name(include_middle=True, include_suffix=False, gender=None):
    """
    Генерирует случайное полное имя.

    Аргументы:
    - include_middle: включать ли второе имя (default: True)
    - include_suffix: включать ли суффикс (Jr., III и т.д.) (default: False)
    - gender: 'male', 'female', или None (любое случайное)
    """

    # Выбор первого имени по полу
    if gender == "male":
        first = random.choice(first_names_male)
    elif gender == "female":
        first = random.choice(first_names_female)
    else:
        first = random.choice(all_first_names)

    # Фамилия
    last = random.choice(last_names)

    # Построение имени
    name_parts = [first]

    # Второе имя (middle name)
    if include_middle and random.random() > 0.3:  # 70% шанс наличия второго имени
        middle = random.choice(middle_names)
        name_parts.append(middle)

    name_parts.append(last)

    # Суффикс
    if include_suffix and random.random() > 0.7:  # 30% шанс суффикса
        suffix = random.choice(suffixes)
        name_parts.append(suffix)

    return " ".join(name_parts)


class ClientsBatch:
    def __init__(self):
        self.clients: set[asyncio.Task] = set()

    def count_active_clients(self) -> int:
        return sum([not c.done() for c in self.clients])

    async def run(
        self,
        port: int,
        room_id: int,
        client_count: int,
        msg_delay: float,
        msg_delay_shift: float,
        logger_path: Path,
    ):

        self.clients = {
            asyncio.create_task(
                run_chat_bot(
                    port=port,
                    room_id=room_id,
                    msg_delay=msg_delay,
                    msg_delay_shift=msg_delay_shift,
                    logger=MessageLoggerImpl(logger_path),
                )
            )
            for _ in range(client_count)
        }

        pending: set[asyncio.Task] = self.clients
        try:
            while pending:
                _, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                self.clients = pending
                print(f"Still have {self.count_active_clients()} clients")

        finally:
            for task in pending:
                task.cancel()


async def run_chat_bot(
    *,
    logger: MessageLogger,
    port: int = 47116,
    room_id: int = 1,
    msg_delay: float = 10,
    msg_delay_shift: float = 10,
):
    username = generate_full_name()
    encoded_username = quote(username)
    uri = f"ws://localhost:{port}/ws/messages/{room_id}/{encoded_username}"

    async def send_messages() -> bool:
        "return True if it needs reconnect, False otherwise"
        print(f"sending messages started {username}")
        try:
            while True:
                text = generate_message()

                if text.strip():
                    sent_monotonic_ns = time.monotonic_ns()
                    await websocket.send(json.dumps({"text": text}))
                    logger.sent(text, sent_monotonic_ns)

                await asyncio.sleep(msg_delay + random.random() * msg_delay_shift)

        except websockets.exceptions.ConnectionClosed:
            print("connection closed")
            return True

        except:
            return False

        finally:
            print(f"sending messages finished {username}")

    cooldown = Cooldown(2.0)

    try:
        while True:
            await cooldown.wait()
            async with websockets.connect(uri) as websocket:
                needs_reconnect = await send_messages()
                if not needs_reconnect:
                    break

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ Connection failed: {e}")

    except ConnectionRefusedError:
        print(f"❌ Server not running on localhost:{port}")

    except asyncio.CancelledError:
        print(f"Cancelled client connection ({username=})")

    finally:
        print(f"Closed client connection ({username=})")


def split_count(total: int, parts: int) -> list[int]:
    """Делит total на parts частей, разница не больше 1."""
    base, rem = divmod(total, parts)
    return [base + (1 if i < rem else 0) for i in range(parts)]


def _run_batch_in_process(
    port: int,
    room_id: int,
    client_count: int,
    msg_delay: float,
    msg_delay_shift: float,
    logger_path: Path,
) -> None:
    """Точка входа для дочернего процесса: свой event loop, свой ClientsBatch."""
    async def _main() -> None:
        try:
            await ClientsBatch().run(
                port,
                room_id,
                client_count,
                msg_delay,
                msg_delay_shift,
                logger_path=logger_path,
            )
        except asyncio.CancelledError:
            pass

    asyncio.run(_main())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", "-i", type=int, default=1, dest="run_id")
    parser.add_argument("--port", "-p", type=int, default=47116)
    parser.add_argument("--room", "-r", type=int, default=1)
    parser.add_argument("--clients", "-c", type=int, default=1)
    parser.add_argument("--processes", "-P", type=int, default=1,
                        help="Number of worker processes to split clients across.")
    parser.add_argument("--delay", type=float, default=10, dest="msg_delay")
    parser.add_argument("--delay-shift", type=float, default=10, dest="msg_delay_shift")
    parsed = parser.parse_args()

    run_id: int = parsed.run_id
    room_id = parsed.room
    client_count: int = parsed.clients
    port: int = parsed.port
    processes: int = parsed.processes

    logger_path = Path("log") / f"spam_bots-{run_id}.txt"

    if processes <= 1:
        # один процесс — можно просто asyncio.run, без mp overhead
        _run_batch_in_process(
            port, room_id, client_count,
            parsed.msg_delay, parsed.msg_delay_shift, logger_path,
        )
        return

    counts = split_count(client_count, processes)

    procs: list[mp.Process] = []
    for i, count in enumerate(counts):
        p = mp.Process(
            target=_run_batch_in_process,
            args=(port, room_id, count, parsed.msg_delay, parsed.msg_delay_shift, logger_path),
            name=f"batch-{i}",
        )
        p.start()
        procs.append(p)
        print(f"Started {p.name} pid={p.pid} with {count} clients")

    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        print("Interrupt received, terminating children...")
        for p in procs:
            if p.is_alive():
                p.terminate()
        for p in procs:
            p.join(timeout=5)
            if p.is_alive():
                p.kill()
                p.join()


if __name__ == "__main__":
    main()
