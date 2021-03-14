class ValueReader:
    @staticmethod
    def read_bytes(bytestream, length):
        raw_bytes = list(map(lambda _: bytestream.get_next_byte(), range(length)))
        safe_bytes = bytes(map(lambda b: 0 if b == b'\xef\xbf\xbd' else b, raw_bytes))
        return (raw_bytes, safe_bytes)
    
    def __init__(self, *args, **kw):
        self.bytes_read = sum(map(lambda b: 1 if type(b) == int else len(b), self.raw_bytes))
        self.bad_bytes = sum(map(lambda b: 1 if b == b'\xef\xbf\xbd' else 0, self.raw_bytes))
        

class ReadNumber(ValueReader, int):
    def __new__(cls, bytestream, length, isSigned):
        (raw_bytes, safe_bytes) = cls.read_bytes(bytestream, length)
        read_number = int.__new__(cls, int.from_bytes(safe_bytes, 'little', signed = isSigned))
        (read_number.raw_bytes, read_number.safe_bytes) = (raw_bytes, safe_bytes)
        return read_number

class ReadText(ValueReader, str):
    def __new__(cls, bytestream, length):
        (raw_bytes, safe_bytes) = cls.read_bytes(bytestream, length)
        read_text = str.__new__(cls, safe_bytes.decode('utf-8'))
        (read_text.raw_bytes, read_text.safe_bytes) = (raw_bytes, safe_bytes)
        return read_text

class InputByteStream:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.bad_bytes = 0

    def get_next_byte(self):
        # Check for the replacement character �, i.e. b'\xef\xbf\xbd'
        next_three_bytes = self.data[self.pos:self.pos+3]
        if next_three_bytes == b'\xef\xbf\xbd':
            self.pos += 3
            self.bad_bytes += 1
            return next_three_bytes
        else:
            self.pos += 1
            return next_three_bytes[0]
    
    def read_byte(self):
        return ReadNumber(self, 1, False)

    def read_int(self):
        return ReadNumber(self, 4, True)

    def read_uint(self):
        return ReadNumber(self, 4, False)
    
    def read_char(self):
        return ReadText(self, 1)
    
    def read_string(self):
        count = 0
        shift = 0
        while True:
            b = self.read_byte()
            assert(b.bad_bytes == 0), "Bad string length byte"
            count = count | (b & 0x7F) << shift
            shift += 7
            if (b & 0x80 == 0):
                break
        
        return ReadText(self, count)

class OutputByteStream:
    def __init__(self):
        self.data = []
    
    def write_number(self, value: int, length, isSigned):
        self.data.append(value.to_bytes(length, 'little', signed = isSigned))
    
    def write_byte(self, value: int):
        self.write_number(value, 1, False)

    def write_int(self, value: int):
        self.write_number(value, 4, True)

    def write_uint(self, value: int):
        self.write_number(value, 4, False)
    
    def write_char(self, value: str):
        self.data.append(value.encode('utf8'))
    
    def write_string(self, value: str):
        strbytes = value.encode('utf8')
        length = len(strbytes)
        while length >= 0x80:
            self.write_byte(length | 0x80)
            length = length >> 7
        
        self.write_byte(length)
        self.data.append(strbytes)
    
    def get_bytes(self):
        return b''.join(self.data)

class IOByteStream:
    def __init__(self, data):
        self.input_stream = InputByteStream(data)
        self.output_stream = OutputByteStream()

    def parse_byte(self):
        read_value = self.input_stream.read_byte()
        self.output_stream.write_byte(read_value)
        return read_value

    def parse_int(self):
        read_value = self.input_stream.read_int()
        self.output_stream.write_int(read_value)
        return read_value

    def parse_uint(self):
        read_value = self.input_stream.read_uint()
        self.output_stream.write_uint(read_value)
        return read_value
    
    def parse_char(self):
        read_value = self.input_stream.read_char()
        self.output_stream.write_char(read_value)
        return read_value
    
    def parse_string(self):
        read_value = self.input_stream.read_string()
        self.output_stream.write_string(read_value)
        return read_value
    
    def get_bytes(self):
        return self.output_stream.get_bytes()

def main():
    filename = "./wheel-representation-5-namelength"
    #filename = "./76561197989820015/wheel-representation-1"
    #filename = "./76561197989820015/proof-of-completeness-1"

    with open(filename + ".solution", "rb") as in_file:
        data: bytes = in_file.read()
    
    stream = IOByteStream(data)

    solution_file_magic_number = stream.parse_uint()
    assert (solution_file_magic_number == 7), "Input is not an Opus Magnum solution."

    puzzle_name = stream.parse_string()
    solution_name = stream.parse_string()
    solved_flag = stream.parse_uint()
    print(f"Puzzle: {puzzle_name}\nSolution: {solution_name}\nIs Solved?: {solved_flag}")
    
    if solved_flag != 0:
        unknown_a = stream.parse_uint()
        cycles = stream.parse_uint()
        unknown_b = stream.parse_uint()
        cost = stream.parse_uint()
        always_2 = stream.parse_uint()
        area = stream.parse_uint()
        always_3 = stream.parse_uint()
        instruction_count = stream.parse_uint()
        print(f"Cycles: {cycles}\nCost: {cost}\nArea: {area}\nInstructions: {instruction_count}")
    
    part_count = stream.parse_uint()
    print(f"Number of Parts: {part_count}")

    for part_num in range(part_count):
        part_name = stream.parse_string()
        always_1 = stream.parse_byte()
        position = (stream.parse_int(), stream.parse_int())
        size = stream.parse_uint()
        rotation = stream.parse_uint()
        index = stream.parse_uint()

        part_instruction_count = stream.parse_uint()
        assert(part_instruction_count.bad_bytes == 0), "Bad instruction_count byte"
        part_instructions = []
        for _ in range(part_instruction_count):
            pos = stream.parse_uint()
            assert(pos.bad_bytes == 0), "Bad instruction position byte"
            instr = stream.parse_char()
            assert(instr.bad_bytes == 0), "Bad instruction byte"
            part_instructions.append((pos, instr))

        track_positions = []
        if part_name == "track":
            track_position_count = stream.parse_uint()
            for _ in range(track_position_count):
                track_positions.append((stream.parse_int(), stream.parse_int()))
        
        arm_number = stream.parse_uint() + 1
        
        conduit_positions = []
        if part_name == "pipe":
            conduit_id = parse_uint()
            conduit_position_count = stream.parse_uint()
            for _ in range(conduit_positions):
                conduit_positions.append((stream.parse_uint(), stream.parse_uint()))
        
        print(f"Part {part_num + 1}: {part_name} at {position} with {part_instruction_count} instructions")

    with open(filename + "-fixed.solution", "wb") as out_file:
        out_file.write(stream.get_bytes())
    print(f"File successfully read! ({stream.input_stream.bad_bytes} bad bytes)")

if __name__ == '__main__':
    main()