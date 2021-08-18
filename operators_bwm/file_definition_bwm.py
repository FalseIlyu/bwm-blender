from io import BufferedReader, BufferedWriter

def read_int16(reader : BufferedReader) -> int:
    return int.int_from_bytes(reader.read(2))

def read_int32(reader : BufferedReader) -> int:
    return int.int_from_bytes(reader.read(4))

class BWMFile:

    '''
     '  Initialisize the data of a BWMFile
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.fileHeader = BWMHeader(reader)
            self.modelHeader = LionheadModelHeader(reader)
            self.materialDefinitions = [
                MaterialDefinition(reader) for i in modelHeader.materialDefinitionCount
            ]
            self.meshDescriptions = [
                MeshDescription(reader) for i in modelHeader.meshDescriptionCount
            ]
            self.bones = [ Bone(reader) for i in modelHeader.boneCount ]
            self.entities = [ Entity(reader) for i in modelHeader.entityCount ]
            self.unknowns1 = [
                Unknown1(reader) for i in modelHeader.unknownCount1
            ]
            self.unknowns2 = [
                Unknown2(reader) for i in modelHeader.unknownCount2
            ]
            self.strides = [ Stride(reader) for i in modelHeader.strideCount ]
            self.vertices = [ Vertex(reader) for i in modelHeader.vertexCount]
            self faces = [ read_int16(reader) for i in modelHeader.indexCount ]
            if fileHeader.version == 6:
                self.modelCleaveCount = read_int32(reader)
                self.modelCleaves = [
                    (
                        read_int32(reader), 
                        read_int32(reader), 
                        read_int32(reader)
                    ) for i in self.modelCleaveCount
                ]

            return

class BWMHeader:
    '''
     '  Header for BWM files, contains identifier for the format 
     '  and information on format version and file size
     '  Size :   0x34
    '''

    def __init__(reader : BufferedReader = None)
        if reader:
            self.fileIdentifier = str(reader.read(40)) # 0x00
            self.size = read_int32(reader) # 0x28
            self.numberIdentifier = read_int32(reader) # 0x2C
            self.version = read_int32(reader) # 0x30
            return

class LionheadModelHeader:
    '''
     '  Part of the Header summarizing information about the model
     '  described by the file
     '  Size :   0x84
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.notHeaderSize = read_int32(reader) # 0x34
            reader.read(64)

            self.materialDefinitionCount = read_int32(reader) # 0x7C
            self.meshDescriptionCount = read_int32(reader) # 0X80
            self.entityCount = read_int32(reader) # 0x84
            self.boneCount = read_int32(reader) # 0x88
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
    def __init__(reader : BufferedReader = None)
        if reader:
            self.diffuseMap = reader.read(64)
            self.lightMap = reader.read(64)
            self.unknown1 = reader.read(64)
            self.specularMap = reader.read(64)
            self.unknown2 = reader.read(64)
            self.normalMap = reader.read(64)
            self.type = reader.read(64)
            return

class MaterialRef:
    '''
     '  Size    :   0x20
    '''
    def __init__(reader : BufferedReader = None)
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

class MeshDescription:
    '''
     '  Size    :   0xD0 + materialRefsCount * 0x20
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.facesCount = read_int32(reader)
            self.indiciesOffset = read_int32(reader)
            self.unknown = reader.read(120)

            self.unknown2 = read_int32(reader)
            self.materialRefsCount = read_int32(reader)
            self.u2 = read_int32(reader)
            self.id = read_int32(reader)
            self.name = reader.read(64)
            self.materialsRefs = [
                MaterialRef(reader) for i in materialsRefsCount
            ]
            return

class Bone:
    '''
     '  Size    :   0x30
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.bone = reader.read(48)
            return

class Entity:
    '''
     '  Size    :   0x130
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.unknown1 = (
                read_int32(reader), 
                read_int32(reader), 
                read_int32(reader)
            )
            self.unknown2 = (
                read_int32(reader), 
                read_int32(reader), 
                read_int32(reader)
            )
            self.unknown3 = (
                read_int32(reader), 
                read_int32(reader), 
                read_int32(reader)
            )
            self.position = (
                read_int32(reader), 
                read_int32(reader), 
                read_int32(reader)
            )
            self.name = reader.read(256)
            return

class Unknown1:
    '''
     '  Size    :   0x0C
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.unknown = reader.read(12)
            return

class Unknown2:
    '''
     '  Size    :   0x0C
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.unknown = reader.read(12)
            return

class Stride:
    '''
     '  Size    :   0x88
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            size = 0x88
            self.count = read_int32(reader)
            self.idSizes = [
                (read_int32(reader), read_int32(reader))
                for i in self.count
            ]
            size = 0x88 - 4 - (8 * self.count)
            unknown = reader.read(size)
            return


class Vertex:
    '''
     '  Size    :   0x20
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.position = (
                read_int32(reader), 
                read_int32(reader),
                read_int32(reader)
            )
            self.normal = (
                read_int32(reader), 
                read_int32(reader),
                read_int32(reader)
            )
            self.u = read_int32(reader)
            self.v = read_int32(reader)
            return

class ModelCleave:
    '''
     '  Size    :   0x0C
    '''
    def __init__(reader : BufferedReader = None)
        if reader:
            self.cleave = (
                reader.read(4),
                reader.read(4),
                reader.read(4)
            )
'''
struct BWMFile
{    

    uint32_t modelCleaveCount;
    uint32_t* modelCleaves;
};
'''