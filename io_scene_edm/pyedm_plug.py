def init():
	pass
def deinit():
	pass
def get_num_alived_objects():
	pass
def get_version():
	return "python dummy version"
def dev_mode():
	return False

def log_error(msg):
	print(f"Error: {msg}")

def log_info(msg):
	print(f"Error: {msg}")

def log_warning(msg):
	print(f"Error: {msg}")

def log_debug(msg):
	print(f"Error: {msg}")


class Model():
	def __init__(self, *args, **kwargs):
		pass

	def getRootTransform(self, *args, **kwargs):
		pass

	def setBBox(self, *args, **kwargs):
		pass

	def setUserBox(self, *args, **kwargs):
		pass

	def setLightBox(self, *args, **kwargs):
		pass

	def save(self, *args, **kwargs):
		pass

	def addRenderNode(self, *args, **kwargs):
		pass

	def addSegmentsNode(self, *args, **kwargs):
		pass

	def addShellNode(self, *args, **kwargs):
		pass

	def addConnector(self, *args, **kwargs):
		pass

	def addLight(self, *args, **kwargs):
		pass

	def getName(self, *args, **kwargs):
		pass

class Node():
	def __init__(self, *args, **kwargs):
		pass

	def getName(self, *args, **kwargs):
		pass

	def addChild(self, *args, **kwargs):
		pass

class Transform(Node):
	def __init__(self, *args, **kwargs):
		pass

	def setMatrix(self, *args, **kwargs):
		pass

class Lod(Node):
	def __init__(self, *args, **kwargs):
		pass

class NumberRoot(Node):
	def __init__(self, *args, **kwargs):
		pass

	def setControls(self, *args, **kwargs):
		pass

class VisibilityNode(Node):
	def __init__(self, *args, **kwargs):
		pass

	def setArguments(self, *args, **kwargs):
		pass

class AnimationNode(Node):
	def __init__(self, *args, **kwargs):
		pass

	def setBaseMatrix(self, *args, **kwargs):
		pass

	def setPositionAnimation(self, *args, **kwargs):
		pass

	def setRotationAnimation(self, *args, **kwargs):
		pass

	def setScaleAnimation(self, *args, **kwargs):
		pass

	def setBasePosition(self, *args, **kwargs):
		pass

	def setBaseRotation(self, *args, **kwargs):
		pass

	def setBaseScale(self, *args, **kwargs):
		pass

class IBlock():
	def __init__(self, *args, **kwargs):
		pass

	def getTypeName(self, *args, **kwargs):
		pass

class BaseBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setPositions(self, *args, **kwargs):
		pass

	def setNormals(self, *args, **kwargs):
		pass

	def setAlbedoMapUV(self, *args, **kwargs):
		pass

	def setAlbedoMap(self, *args, **kwargs):
		pass

	def setAlbedoMapUVShift(self, *args, **kwargs):
		pass

class ColorBaseBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setPositions(self, *args, **kwargs):
		pass

	def setNormals(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

class FlirBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setFlirMap(self, *args, **kwargs):
		pass

class DamageBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setAlbedoMapUV(self, *args, **kwargs):
		pass

	def setNormalMapUV(self, *args, **kwargs):
		pass

	def setPerVertexArguments(self, *args, **kwargs):
		pass

	def setAlbedoMap(self, *args, **kwargs):
		pass

	def setNormalMap(self, *args, **kwargs):
		pass

	def setMask(self, *args, **kwargs):
		pass

	def setMaskRGBA(self, *args, **kwargs):
		pass

	def setArgument(self, *args, **kwargs):
		pass

class BoneBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setBoneWeights(self, *args, **kwargs):
		pass

	def setBoneIndices(self, *args, **kwargs):
		pass

	def setBones(self, *args, **kwargs):
		pass

	def getBoneNames(self, *args, **kwargs):
		pass

	def setBoneNames(self, *args, **kwargs):
		pass

	def setSkinBox(self, *args, **kwargs):
		pass

class NumberBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setUVParams(self, *args, **kwargs):
		pass

class EmissiveBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setEmissiveMap(self, *args, **kwargs):
		pass

	def setEmissiveMapUV(self, *args, **kwargs):
		pass

	def setAmount(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

	def setEmissiveType(self, *args, **kwargs):
		pass

	def setUVShift(self, *args, **kwargs):
		pass

class EmissiveColorBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

	def setAmount(self, *args, **kwargs):
		pass

class AoBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setAoMap(self, *args, **kwargs):
		pass

	def setAoMapUV(self, *args, **kwargs):
		pass

	def setAoShift(self, *args, **kwargs):
		pass

	def setAoAnimationArgument(self, *args, **kwargs):
		pass

class DecalBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setDecalMap(self, *args, **kwargs):
		pass

	def setDecalMapUV(self, *args, **kwargs):
		pass

	def setDecalShift(self, *args, **kwargs):
		pass

class NormalBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setNormalMap(self, *args, **kwargs):
		pass

	def setNormalMapUV(self, *args, **kwargs):
		pass

class AormsBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setAormsMap(self, *args, **kwargs):
		pass

	def setAormsMapUV(self, *args, **kwargs):
		pass

class GlassFilterBlock(IBlock):
	def __init__(self, *args, **kwargs):
		pass

	def setColorMap(self, *args, **kwargs):
		pass

	def setInstrumental(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

class IRenderNode():
	def __init__(self, *args, **kwargs):
		pass

	def hasBlock(self, *args, **kwargs):
		pass

class FakeOmniLight():
	def __init__(self, *args, **kwargs):
		pass

	def setPos(self, *args, **kwargs):
		pass

	def setUV(self, *args, **kwargs):
		pass

	def setSize(self, *args, **kwargs):
		pass

class FakeOmniLights(IRenderNode):
	def __init__(self, *args, **kwargs):
		pass

	def set(self, *args, **kwargs):
		pass

	def setTexture(self, *args, **kwargs):
		pass

	def setMinSizeInPixels(self, *args, **kwargs):
		pass

	def setMaxDistance(self, *args, **kwargs):
		pass

	def setLuminance(self, *args, **kwargs):
		pass

	def setShiftToCamera(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class AnimatedFakeOmniLight(FakeOmniLights):
	def __init__(self, *args, **kwargs):
		pass

	def setAnimationArg(self, *args, **kwargs):
		pass

	def setLightsAnimation(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class FakeSpotLight():
	def __init__(self, *args, **kwargs):
		pass

	def setPos(self, *args, **kwargs):
		pass

	def setUV(self, *args, **kwargs):
		pass

	def setSize(self, *args, **kwargs):
		pass

	def setBackUV(self, *args, **kwargs):
		pass

	def setDirection(self, *args, **kwargs):
		pass

	def setBackSide(self, *args, **kwargs):
		pass

class FakeSpotLights(IRenderNode):
	def __init__(self, *args, **kwargs):
		pass

	def set(self, *args, **kwargs):
		pass

	def setTexture(self, *args, **kwargs):
		pass

	def setMinSizeInPixels(self, *args, **kwargs):
		pass

	def setMaxDistance(self, *args, **kwargs):
		pass

	def setLuminance(self, *args, **kwargs):
		pass

	def setShiftToCamera(self, *args, **kwargs):
		pass

	def setConeSetup(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class AnimatedFakeSpotLight(FakeSpotLights):
	def __init__(self, *args, **kwargs):
		pass

	def setAnimationArg(self, *args, **kwargs):
		pass

	def setLightsAnimation(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class SegmentsNode():
	def __init__(self, *args, **kwargs):
		pass

	def set(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class ShellNode():
	def __init__(self, *args, **kwargs):
		pass

	def setIndices(self, *args, **kwargs):
		pass

	def setPositions(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class Connector():
	def __init__(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

	def setPropertyFloat(self, *args, **kwargs):
		pass

	def setPropertyString(self, *args, **kwargs):
		pass

class ILight():
	def __init__(self, *args, **kwargs):
		pass

	def setVolumeRadiusFactor(self, *args, **kwargs):
		pass

	def setVolumeDensityFactor(self, *args, **kwargs):
		pass

	def setVolumeNearDistance(self, *args, **kwargs):
		pass

	def setVolumeType(self, *args, **kwargs):
		pass

class OmniLight(ILight):
	def __init__(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

	def setBrightness(self, *args, **kwargs):
		pass

	def setDistance(self, *args, **kwargs):
		pass

	def setSpecularAmount(self, *args, **kwargs):
		pass

	def setSoftness(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class SpotLight(ILight):
	def __init__(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

	def setBrightness(self, *args, **kwargs):
		pass

	def setDistance(self, *args, **kwargs):
		pass

	def setPhi(self, *args, **kwargs):
		pass

	def setTheta(self, *args, **kwargs):
		pass

	def setAngles(self, *args, **kwargs):
		pass

	def setSpecularAmount(self, *args, **kwargs):
		pass

	def setSoftness(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class Bone(Node):
	def __init__(self, *args, **kwargs):
		pass

	def setMatrix(self, *args, **kwargs):
		pass

	def getName(self, *args, **kwargs):
		pass

	def setInvertedBaseBoneMatrix(self, *args, **kwargs):
		pass

class PropertyFloat():
	def __init__(self, *args, **kwargs):
		pass

	def set(self, *args, **kwargs):
		pass

	def setAnim(self, *args, **kwargs):
		pass

class PropertyFloat2():
	def __init__(self, *args, **kwargs):
		pass

	def set(self, *args, **kwargs):
		pass

	def setAnim(self, *args, **kwargs):
		pass

class PropertyFloat3():
	def __init__(self, *args, **kwargs):
		pass

	def set(self, *args, **kwargs):
		pass

	def setAnim(self, *args, **kwargs):
		pass

class PBRNode(IRenderNode):
	def __init__(self, *args, **kwargs):
		pass

	def getName(self, *args, **kwargs):
		pass

	def setIndices(self, *args, **kwargs):
		pass

	def setShadowCaster(self, *args, **kwargs):
		pass

	def setTransparentMode(self, *args, **kwargs):
		pass

	def setOpacityValue(self, *args, **kwargs):
		pass

	def setDecalId(self, *args, **kwargs):
		pass

	def addBlock(self, *args, **kwargs):
		pass

	def setTwoSided(self, *args, **kwargs):
		pass

	def setPurposeWaterMask(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

	def getBlock(self, *args, **kwargs):
		pass

	def addTransparentPivot(self, *args, **kwargs):
		pass

class GlassNode(PBRNode):
	def __init__(self, *args, **kwargs):
		pass

	def setTransparentMode(self, *args, **kwargs):
		pass

	def setGlassType(self, *args, **kwargs):
		pass

class MirrorNode(IRenderNode):
	def __init__(self, *args, **kwargs):
		pass

	def setPositions(self, *args, **kwargs):
		pass

	def setNormals(self, *args, **kwargs):
		pass

	def setIndices(self, *args, **kwargs):
		pass

	def setTexture(self, *args, **kwargs):
		pass

	def setTextureCoordinates(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class ColorNode(IRenderNode):
	def __init__(self, *args, **kwargs):
		pass

	def setPositions(self, *args, **kwargs):
		pass

	def setNormals(self, *args, **kwargs):
		pass

	def setIndices(self, *args, **kwargs):
		pass

	def setColor(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass

class DeckNode(IRenderNode):
	def __init__(self, *args, **kwargs):
		pass

	def setPositions(self, *args, **kwargs):
		pass

	def setNormals(self, *args, **kwargs):
		pass

	def setBaseTiledMap(self, *args, **kwargs):
		pass

	def setNormalTiledMap(self, *args, **kwargs):
		pass

	def setAormsTiledMap(self, *args, **kwargs):
		pass

	def setBaseMap(self, *args, **kwargs):
		pass

	def setAormsMap(self, *args, **kwargs):
		pass

	def setDamageMap(self, *args, **kwargs):
		pass

	def setDamageMask(self, *args, **kwargs):
		pass

	def setDamageMaskRGBA(self, *args, **kwargs):
		pass

	def setTiledUV(self, *args, **kwargs):
		pass

	def setRegularUV(self, *args, **kwargs):
		pass

	def setRainMask(self, *args, **kwargs):
		pass

	def setIndices(self, *args, **kwargs):
		pass

	def setTransparentMode(self, *args, **kwargs):
		pass

	def setDecalId(self, *args, **kwargs):
		pass

	def setArgument(self, *args, **kwargs):
		pass

	def setPerVertexArguments(self, *args, **kwargs):
		pass

	def setControlNode(self, *args, **kwargs):
		pass
