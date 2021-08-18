from io import BufferedReader

def read_int32(reader : BufferedReader) -> int:
    return int.int_from_bytes(reader.read(3))

class BWMFile:

    def readInit(filepath):
        with open(filepath, 'rb') as file:
          self.fileHeader = BWMHeader.readInit(file)
          self.modelHeader = BWMHeader.readInit(file)
        return self

class BWMHeader:
    '''
     '  Header for BWM files, contains identifier for the format 
     '  and information on format version and file size
     '  Size :   0x34
    '''

    def readInit(reader : BufferedReader):

        self.fileIdentifier = str(reader.read(40)) # 0x00
        self.size = read_int32(reader) # 0x28
        self.numberIdentifier = read_int32(reader) # 0x2C
        self.version = read_int32(reader) # 0x30
        return self

class LionheadModelHeader:
    '''
     '  Part of the Header summarizing information about the model
     '  described by the file
     '  Size :   0x84
    '''

    def readInit(reader : BufferedReader):
        
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
        
#class MaterialDefinition:
    

'''
struct BWMFile
{

    struct MaterialDefinition
    {
        /**
         * Size :   0x1C0
         * */
        char diffuseMap[64];
        char lightMap[64];
        char unknown1[64];
        char specularMap[64];
        char unknown2[64];
        char normalMap[64];
        char Type[64];
    } *materialDefinitions;

    struct MeshDescription
    {
        /**
         * Size :   0xD0 + materialRefsCount * 0x20
         * */
        uint32_t facesCount;
        uint32_t indiciesOffset;
        char unknown[120];

        uint32_t unkown2;
        uint32_t materialRefsCount;
        uint32_t U2;
        uint32_t ID;
        char name[64];
        // 8 bytes of unknown data

        struct MateralRef
        {
            /**
             * Size :   0x20
             * */
            uint32_t materialDefinition;
            uint32_t indiciesOffset;
            uint32_t indiciesSize;
            uint32_t vertexOffset;
            uint32_t vertexSize;
            uint32_t facesOffset;
            uint32_t facesSize;
            uint32_t unknown;
        }* materialsRefs;
    }* meshDescriptions;
    
    struct Bones
    {
        /**
         * Size :   0x30
         * */
        // 48 bytes of unknown data
    };
    
    struct Entity
    {
        /**
         * Size :   0x130
         * */
        uint32_t unknown1[3];
        uint32_t unknown2[3];
        uint32_t unknown3[3];
        uint32_t position[3];
        char name[256];
    }* entities;

    struct Unknown1
    {
        /**
         * Size :   0x0C
         * */
        // 12 bytes of unknown data
    }* unknowns1;
    

    struct unknown2
    {
        /**
         * Size :   0x0C
         * */
        // 12 bytes of unknown data
    }* unknowns2;
    
    struct Stride
    {
        /**
         * Size :   0x88
         * */
        uint32_t count;
        uint32_t* idSizes;
        char* unknown;
    }* strides;

    struct Vertex
    {
        /**
         * Size :   0x20
         * */
        uint32_t position[3];
        uint32_t position[3];
        uint32_t U;
        uint32_t V;

    }* verticies;

    uint32_t* indices;

    uint32_t modelCleaveCount;
    uint32_t* modelCleaves;
};
'''