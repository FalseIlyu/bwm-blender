from io import BufferedReader
import struct
from typing import List


def read_float(reader : BufferedReader) -> float:
    return struct.unpack('f', reader.read(4))[0]


def read_int16(reader : BufferedReader) -> int:
    return int.from_bytes(reader.read(2), byteorder='little')


def read_int32(reader : BufferedReader) -> int:
    return int.from_bytes(reader.read(4), byteorder='little')


strideFormat = [4, 12, 8, 4, 1]


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
            self.collisionPoints = [
                collisionPoint(reader) for i in range(self.modelHeader.collisionPointCount)
            ]
            self.strides = [
                Stride(reader) for i in range(self.modelHeader.strideCount)
            ]
            self.vertices = [ 
                Vertex(self.strides[0], reader) for vertex in range(self.modelHeader.vertexCount)
            ]
            self.data = [ 
                [
                    stride.read_data(reader) 
                    for vertex in range(self.modelHeader.vertexCount)
                    ] 
                    for stride in self.strides[1:]
            ]
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
            self.fileIdentifier = (reader.read(40)).decode('utf-8') # 0x00
            if "LiOnHeAdMODEL" not in self.fileIdentifier:
                raise ValueError("This is not a valid .bwm file (magic string mismatch).")
            self.size = read_int32(reader) # 0x28
            self.numberIdentifier = read_int32(reader) # 0x2C
            if self.numberIdentifier != 0x2B00B1E5:
                raise ValueError("This is not a valid .bwm file (magic number mismatch).")
            self.version = read_int32(reader) # 0x30
            if self.version < 5:
                raise ValueError("Unsupported version of the format")
            self.metadataSize = read_int32(reader) # 0x34
            # 0x38 + metadataSize = vertexPointer
            return


class LionheadModelHeader:
    '''
     '  Part of the Header summarizing information about the model
     '  described by the file
     '  Size :   0x80
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.unknown1 = tuple( read_int32(reader) for i in range(3) )
            self.unknown_int1 = read_int32(reader) # Must be != 0 for the model to show ingame
            self.unknown2 = tuple( read_int32(reader) for i in range(10) )
            self.unknown_int2 = read_int32(reader) # Snappin related value (maybe distance)
            self.unknown3 = tuple( read_int32(reader) for i in range(2) )

            self.materialDefinitionCount = read_int32(reader) # 0x7C
            self.meshDescriptionCount = read_int32(reader) # 0X80
            self.boneCount = read_int32(reader) # 0x84
            self.entityCount = read_int32(reader) # 0x88
            self.unknownCount1 = read_int32(reader) # 0x8C
            self.collisionPointCount = read_int32(reader) # 0x90

            self.unknown2 = tuple( read_int32(reader) for i in range(5) )

            self.vertexCount = read_int32(reader) # 0xA8
            self.strideCount = read_int32(reader) # 0xAC
            self.type = read_int32(reader) # 0xB0 Three for skins and two for the rest
            self.indexCount = read_int32(reader) # 0xB4 
            return
        

class MaterialDefinition:
    '''
     '  Size    :   0x1C0
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.diffuseMap = reader.read(64).decode('utf-8')
            self.lightMap = reader.read(64).decode('utf-8')
            self.unknown1 = reader.read(64).decode('utf-8')
            self.specularMap = reader.read(64).decode('utf-8')
            self.unknown2 = reader.read(64).decode('utf-8')
            self.normalMap = reader.read(64).decode('utf-8')
            self.type = reader.read(64).decode('utf-8')
            return


class MeshDescription:
    '''
     '  Size    :   0xD8 + materialRefsCount * 0x20
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.facesCount = read_int32(reader)
            self.indiciesOffset = read_int32(reader)
            self.indiciesSize = read_int32(reader)
            self.vertexOffset = read_int32(reader)
            self.vertexSize = read_int32(reader)
            self.axis1 = struct.unpack('<fff', reader.read(12))
            self.axis2 = struct.unpack('<fff', reader.read(12))
            self.axis3 = struct.unpack('<fff', reader.read(12))
            self.position = struct.unpack('<fff', reader.read(12))
            self.unknown1 = reader.read(60)
            self.unknown_int = read_int32(reader)
            self.unknown2 = reader.read(4)
            self.materialRefsCount = read_int32(reader)
            self.u2 = read_int32(reader)
            self.id = read_int32(reader)
            self.name = reader.read(64).decode('utf-8')
            reader.read(8)
            
            self.materialRefs : List[MaterialRef] = []

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
            self.unknown = read_float(reader)
            return


class Bone:
    '''
     '  Size    :   0x30
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.axis1 = (read_float(reader), read_float(reader), read_float(reader))
            self.axis2 = (read_float(reader), read_float(reader), read_float(reader))
            self.axis3 = (read_float(reader), read_float(reader), read_float(reader))
            self.position = (read_float(reader), read_float(reader), read_float(reader))
            return


class Entity:
    '''
     '  Size    :   0x130
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.axis1 = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.axis2 = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.axis3 = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.position = (
                read_float(reader), 
                read_float(reader), 
                read_float(reader)
            )
            self.name = reader.read(256).decode('utf-8')
            return


class Unknown1:
    '''
     '  Size    :   0x0C
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.unknown = struct.unpack('<fff', reader.read(12))
            return


class collisionPoint:
    '''
     '  Size    :   0x0C
    '''
    def __init__(self, reader : BufferedReader = None):
        if reader:
            self.unknown = struct.unpack('<fff', reader.read(12))
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
    
    def read_data(self, reader : BufferedReader):
        return reader.read(self.stride)


class Vertex:
    '''
     '  Size    :   0x20
    '''
    def __init__(self, stride: Stride, reader : BufferedReader = None):
        if reader:
            self.uvs = []
            for (id, format) in stride.idSizes:
                if id == 0:
                    self.position = (
                        read_float(reader),
                        read_float(reader),
                        read_float(reader)
                    )
                if id == 1:
                    self.normal = (
                        read_float(reader),
                        read_float(reader),
                        read_float(reader)
                    )
                if id == 2:
                    self.uvs.append(
                        (read_float(reader), read_float(reader))
                    )
            return


if __name__ == "__main__":

    # test call
    with open("G:\\Lionhead Studios\\Black & White 2\\Data\\Art\\models\\m_greekstoragepit.bwm", "rb") as testBWM:
        file = BWMFile(testBWM)
        pass