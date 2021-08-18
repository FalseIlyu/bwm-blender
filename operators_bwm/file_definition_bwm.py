from io import BufferedReader, BufferedWriter
import struct

def read_float(reader : BufferedReader) -> float:
    return struct.unpack('f', reader.read(4))[0]

def read_int16(reader : BufferedReader) -> int:
    return int.from_bytes(reader.read(2), byteorder='little')

def read_int32(reader : BufferedReader) -> int:
    return int.from_bytes(reader.read(4), byteorder='little')

class BWMFile:

    '''
     '  Initialisize the data of a BWMFile
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.fileHeader = BWMHeader(reader)
            self.modelHeader = LionheadModelHeader(reader)
            self.materialDefinitions = [
                MaterialDefinition(reader) 
                for i in range(self.modelHeader.materialDefinitionCount)
            ]
            self.meshDescriptions = [
                MeshDescription(reader) 
                for i in range(self.modelHeader.meshDescriptionCount)
            ]
            for mesh in self.meshDescriptions:
                mesh.materialRefs = [
                    MaterialRef(reader) for i in range(mesh.materialRefsCount)
                ]
            self.bones = [
                Bone(reader) for i in range(self.modelHeader.boneCount)
            ]
            self.entities = [
                Entity(reader) for i in range(self.modelHeader.entityCount)
            ]
            self.unknowns1 = [
                Unknown1(reader) for i in range(self.modelHeader.unknownCount1)
            ]
            self.unknowns2 = [
                Unknown2(reader) for i in range(self.modelHeader.unknownCount2)
            ]
            self.strides = [
                Stride(reader) for i in range(self.modelHeader.strideCount)
            ]
            self.vertices = []
            for stride in self.strides:
                self.vertices.append([
                    Vertex(stride, reader) for i in range(self.modelHeader.vertexCount)
                ])
            self.indexes = [
                read_int16(reader) for i in range(self.modelHeader.indexCount)
            ]
            if self.fileHeader.version > 5:
                self.modelHeader.modelCleaveCount = read_int32(reader)
                self.modelCleaves = [
                    (
                        read_float(reader), 
                        read_float(reader), 
                        read_float(reader)
                    ) for i in range(self.modelHeader.modelCleaveCount)
                ]

            return

class BWMHeader:
    '''
     '  Header for BWM files, contains identifier for the format 
     '  and information on format version and file size
     '  Size :   0x38
    '''

    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.fileIdentifier = str(reader.read(40)) # 0x00
            self.size = read_int32(reader) # 0x28
            self.numberIdentifier = read_int32(reader) # 0x2C
            self.version = read_int32(reader) # 0x30
            self.notHeaderSize = read_int32(reader) # 0x34
            return

class LionheadModelHeader:
    '''
     '  Part of the Header summarizing information about the model
     '  described by the file
     '  Size :   0x80
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            reader.read(68)

            self.materialDefinitionCount = read_int32(reader) # 0x7C
            self.meshDescriptionCount = read_int32(reader) # 0X80
            self.boneCount = read_int32(reader) # 0x84
            self.entityCount = read_int32(reader) # 0x88
            self.unknownCount1 = read_int32(reader) # 0x8C
            self.unknownCount2 = read_int32(reader) # 0x90
            reader.read(20)

            self.vertexCount = read_int32(reader) # 0xA8
            self.strideCount = read_int32(reader) # 0xAC
            reader.read(4)

            self.indexCount = read_int32(reader) # 0xB4 
            return
        
class MaterialDefinition:
    '''
     '  Size    :   0x1C0
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.diffuseMap = reader.read(64)
            self.lightMap = reader.read(64)
            self.unknown1 = reader.read(64)
            self.specularMap = reader.read(64)
            self.unknown2 = reader.read(64)
            self.normalMap = reader.read(64)
            self.type = reader.read(64)
            return

class MeshDescription:
    '''
     '  Size    :   0xD8 + materialRefsCount * 0x20
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.facesCount = read_int32(reader)
            self.indiciesOffset = read_int32(reader)
            self.unknown = reader.read(124)

            self.unknown2 = read_int32(reader)
            self.materialRefsCount = read_int32(reader)
            self.u2 = read_int32(reader)
            self.id = read_int32(reader)
            self.name = reader.read(64)
            reader.read(8)

            return

class MaterialRef:
    '''
     '  Size    :   0x20
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.materialDefinition = read_int32(reader)
            self.indiciesOffset = read_int32(reader)
            self.indiciesSize = read_int32(reader)
            self.vertexOffset = read_int32(reader)
            self.vertexSize = read_int32(reader)
            self.facesOffset = read_int32(reader)
            self.facesSize = read_int32(reader)
            self.unknown = read_int32(reader)
            return

class Bone:
    '''
     '  Size    :   0x30
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.bone = reader.read(48)
            return

class Entity:
    '''
     '  Size    :   0x130
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.unknown1 = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.unknown2 = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.unknown3 = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.position = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.name = reader.read(256)
            return

class Unknown1:
    '''
     '  Size    :   0x0C
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.unknown = reader.read(12)
            return

class Unknown2:
    '''
     '  Size    :   0x0C
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.unknown = reader.read(12)
            return

class Stride:
    '''
     '  Size    :   0x88
    '''
    def __init__(self, reader : BufferedReader = None):
        stride_format = [ 4, 8, 12, 4, 1 ]
        if reader:
            size = 0x88
            self.count = read_int32(reader)
            self.idSizes = [
                (read_int32(reader), read_int32(reader))
                for i in range(self.count)
            ]
            self.stride = 0
            for (id, ssize) in self.idSizes:
                self.stride = self.stride + stride_format[ssize]
            size = 0x88 - 4 - (8 * self.count)
            self.unknown = reader.read(size)
            return


class Vertex:
    '''
     '  Size    :   0x20
    '''
    def __init__(self, stride : Stride, reader : BufferedReader = None):
        if reader:
            self.position = (
                read_float(reader), 
                read_float(reader),
                read_float(reader)
            )
            self.normal = (
                read_float(reader), 
                read_float(reader),
                read_float(reader)
            )
            self.u = read_float(reader)
            self.v = read_float(reader)

            if stride.stride > 32:
                reader.read(stride.stride - 32)
            return

if __name__ == "__main__":

    # test call
    with open("G:\\Lionhead Studios\\Black & White 2\\Data\\Art\\models\\m_greek_catapultworkshop.bwm", "rb") as testBWM:
        BWMFile(testBWM)