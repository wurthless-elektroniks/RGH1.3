'''
whatsmyinstall - identify your RGH1.3 install type
'''

import os
import sys
import hashlib

import ecc
import smc

# importing a private function... very shitty code
from convert_rgh13 import _extract_loaders

from make_smcs import Rgh13BuildType

# pulled from git commit history. pray your install matches one of these...
OLD_SMC_FINGERPRINTS = {
    # rgh13_xenon.bin
	'cc520326cc585f8185100c70c82fe242524168f9': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'bafcd494f9169b70b37ebd5e6ccc1823cae774c0': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f680fa0d4fcb924472beb99048a96835b9909508': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'a499b16dfe03258e2d6e830f1c6a7540d99b5901': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'7531b7cf9707d64945acb3e6ecb8390eb9df9ab4': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'5523558355181ea05486e1f31cd12210d603e150': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'31a59f916e8e96798afd839ab01909df98e4f8ee': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f680fa0d4fcb924472beb99048a96835b9909508': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f52f4231df0dc18c7318426a7fc1a587598ce2ad': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'c69930e4be2f9dc555cd9e0ca8dccb723da47eb3': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'63acaab84af2960b462286812e3da30539b0e558': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'75d1702af9ea1645cb3c2a65d63fdb5fc5cd3573': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f628d214d97f1ec6d5799f663c0ef235993799af': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'6c3c9f1ef50e45107b4192ffb31bdd11c3ed0a0a': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'51f22df6222ddb3ca453b7306b89977c9aba6b48': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f98f02a06cb694fb23b1703a5e8e421df1c715c0': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'6f661ab2f6acd6dcaae4ccb4fc81c6ffebfaa002': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'7531b7cf9707d64945acb3e6ecb8390eb9df9ab4': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f69df5a1ea374419c1a0ddf785e8855441dbde36': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	# rgh13_xenon_1wire.bin
	'83e9cf57f6b7f0a0011e3751815bafebb367965d': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'bc082f8eb502edccadbeaf9c4a90d403a49bc1b3': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'3b8ca8da00a194a20f1dc86176cc7a7cde74c6b5': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'4f6e3e7e8107c51e94597b678c8d70b7c2542513': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'c0ac9838e0c484f549673bfd38cb50119bdab642': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'1fa637d7e4ee523be3815900fda7aeab42b0b642': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'47e94e0ee41dbb806ab020545f8eb5a89d48a3e7': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'bc082f8eb502edccadbeaf9c4a90d403a49bc1b3': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'4f6e3e7e8107c51e94597b678c8d70b7c2542513': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'15cbca923d42933d58fa54a09764f816db479603': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'42b294265d9b6d529327591a4aa53190af647938': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f5226e1291fe17710c0252a577517499b7bad419': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	# rgh13_xenon_0wire.bin
	'01c5b14cb6ea085a68c03ae17a1f8b6f6a9d942c': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'e7328aec61a2fd1a4660fdb79ac6be6a841c6759': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'0250e6f3fc31cd7fe8b382b78700aa741f538a25': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'2f96bb6ae07bfbbb1728a9cbce428195322ee8e7': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'344fc687ba6c9680971445d99ffe4fe6cec27b8b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'13ce0596f0be360e25a4c27f82cfe861c96a8735': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'32f8ec030753672cdc69e4bdf9760a5ee3e0ce9d': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'9932962dd0291540a766602726433702cf1fbe55': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'697458a0c6b4f3a0b726fafda0753bf05431660e': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'698a1b197e27845091120d2efa5cd2360f2af23f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'698a1b197e27845091120d2efa5cd2360f2af23f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'b42188b67d0da77953054c312fdcd16e9966aa62': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'01c5b14cb6ea085a68c03ae17a1f8b6f6a9d942c': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'ccfb0f9ce4fda3c1caf6200a269c2fa7f1839c84': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	# rgh13_jasper.bin
	'74f1c0710755562af372f852441658839fcbc61d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'bc16bdac451632f05a7fd749e1707cc5475c4834': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'fd5063ac06516b6273f162f7784cc712b330040b': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'16a58baf7a149ce5c5d122180123c7fa9dc943f7': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'f80eb38a418825391de657df6dbeb878fa6fa5cb': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'25ad42b17aa9bccc7d9aebc2d2c39ed844b93885': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'7347e42de1461e2b13ae56c11374542c32317cb3': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'fa22f73bf01c48dce9d5ac47df6a8c0f9bb6e65d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'a7745dc7b6280651f3e86ce54a0d8f769b4c69bd': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'513d7dd59d494229fe6400c9abc85c6c1419eb51': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'859c827ccbd16e45a523847a0e99f77a9d6964ec': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'971c5d23115390023811c98c5160c91ccb4180aa': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'47b192ed2d958a8f0da1f4d000d5231ba65d23fc': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'f94ece19d0eb9a8380081408297f2f2e2e1b0da3': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'b0cba7d1d42f1f6480fa92b311892301b92c529b': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'79a15464a59f5703f99d68309023cfb8d74c0639': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'0f121daa17a2d1c70daf7c4b2c6e06d6ffe2b379': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'329fa56167a347117ce252fb2974952fddf6db5b': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'0f121daa17a2d1c70daf7c4b2c6e06d6ffe2b379': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'c5abdcc1706507b13605ab483fe7c9b225c1bfde': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'1337526a7e4da1e93d51bcd877ffb1e4bc39f2f2': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'7347e42de1461e2b13ae56c11374542c32317cb3': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'ad6d8bd5bcbb26c2ceacf937d980059c0ea42d32': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'78fa6c78d3a755f2ec94a90a42275544fef69070': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	# rgh13_badjasper.bin
	'6a631402f2ec065388e7b147d483517973e9c180': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'e02e4021056af75ad94456100ebc2a458fe9f79e': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'4711473febd125465157ba47c474e7b7da604bf2': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'3a8e7679396016af2f0e9297f901ef2f7139492c': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'51ab12aca2326861a21214ba2841632f6ff60d89': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'51ab12aca2326861a21214ba2841632f6ff60d89': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'd52d9c45f4adb609e3ae545a1a307601669161c9': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'582cd88cff73d31df1821e39339e96c236f4762b': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'02afbf783be6fca01d6425bd5dce191c88a87fe5': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'3fd417409daa9a21e2ded0d46fdc56fdecbffa0d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'94be0060b8917acba6cd88b4aa4469ff21d3b995': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'7f4da533634024bb2e16f8a0367770518457f43c': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'98e0e56f73ef546022955ae088afb3bde47e93bf': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'd52d9c45f4adb609e3ae545a1a307601669161c9': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'403592a5722b9f450012b50d5a6f8b37aa50ca90': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'bc43f94e41dc9dd6ac958b81d462262d37ae1ae9': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'7e7aff914602e0248d4461061d13b5a7cb3a2075': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'b8ca72bb7e90ef396373e7b6a1941f527b684606': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'723794d6f910480824eae51a0fa4c36887c470a3': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'22b1ea423ddfc31cbe721b6f0a98a6e1f3393dc7': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'c5a329730710f5063603ebc62daa495b0ce86f66': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'aac8eb92b2c04c1b7b9652ad3577a8fce8f0d003': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'8403ad7d6cc258b82f4cf8d1c02f15ff7065c05f': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'039c7593fbc92e158afec9711f6fca57c73e2b65': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	# rgh13_jasper_for_falcon.bin
	'75bea5c2fa1dfb627c2309d6faa9f6389c686e9f': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'71e31d30eb01bedafdff658d577a61eed3632f30': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'9dc3259e6cde9fe0061df32ed49b38bd2a0aae6e': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'35e8520f1292d6ca02c6460f87c7cbd54870c282': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'4155f54795d4d3fa47790bc9780d7e4330376b10': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'b226458d26783e68292a5857537e5f13f7ca2f7c': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'f91c5edbcc1d3917cf0fd716a6acc281325937a9': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'cbacee9dbac67387b6c5c351f2112ae3db4158cc': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'35e8520f1292d6ca02c6460f87c7cbd54870c282': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'f4505db9fd9ad41e256a04beeca8e413b7f69628': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'e1981703e0152c425320589e294cbe5e7ac3e4a3': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'3d1e9999f40e23cb24df00a4c240353b514b5a83': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'4155f54795d4d3fa47790bc9780d7e4330376b10': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'09bf2b899c37c3006401a5ca674c57ceba58072d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'559e300a4dc80135440e8b1505adb2969339941f': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'51470fd1f5daf06a6486296356a9c308343840d5': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'500ccdc7ec670797fe0e00cab11a730e8b7daa6b': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	# rgh13_badjasper_for_falcon.bin
	'199edbb016d523d3812eaa35cce8e5818408b5d0': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'41656d9a3655f467d83efdc4f63e333b508c3582': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'307618b8911b47ccbb547aab9183e84f324e2415': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'2c3e55a3334613b78acefa2edbfcf39a42235bcd': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'199edbb016d523d3812eaa35cce8e5818408b5d0': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'057150255c0d654b58f6cea9f0a08b1a0342783d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'88acfb7e5ae253f3f9b550aaa6e51afa0c5eb265': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'e8a96ad1e3fab308effda0b042751388e8593cb8': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'569ba9a4abad487720d1737e29bf99270b5939df': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'06f7946b68e1db270179f66d177fe908ab0950ae': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'9026d9a137816c1069d4de9ec0f7a2bdb9eaeb71': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'616cdae6206b0ab6d6712e14f5f2a9c4311d2994': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'1a92c7ff86bf338e27f0b3748b154aa26d48acc8': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'8600425e4bbe1996bebaf57c7b2b6b6b4022a55d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'41656d9a3655f467d83efdc4f63e333b508c3582': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'4d270f35a719f4075c02ba0506446bde98f13097': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'ce5ceb7911b04df557dd36d377907254d1f62c67': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	# rgh13_jasper_for_zephyr.bin
	'35e8520f1292d6ca02c6460f87c7cbd54870c282': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'cbacee9dbac67387b6c5c351f2112ae3db4158cc': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'e1981703e0152c425320589e294cbe5e7ac3e4a3': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'09bf2b899c37c3006401a5ca674c57ceba58072d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'4155f54795d4d3fa47790bc9780d7e4330376b10': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'9dc3259e6cde9fe0061df32ed49b38bd2a0aae6e': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'35e8520f1292d6ca02c6460f87c7cbd54870c282': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'4155f54795d4d3fa47790bc9780d7e4330376b10': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'f91c5edbcc1d3917cf0fd716a6acc281325937a9': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	'500ccdc7ec670797fe0e00cab11a730e8b7daa6b': { 'type': Rgh13BuildType.TILTSW, 'badjasper': False },
	# rgh13_badjasper_for_zephyr.bin
	'4d270f35a719f4075c02ba0506446bde98f13097': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'41656d9a3655f467d83efdc4f63e333b508c3582': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'1a92c7ff86bf338e27f0b3748b154aa26d48acc8': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'199edbb016d523d3812eaa35cce8e5818408b5d0': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'41656d9a3655f467d83efdc4f63e333b508c3582': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'e8a96ad1e3fab308effda0b042751388e8593cb8': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'307618b8911b47ccbb547aab9183e84f324e2415': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'057150255c0d654b58f6cea9f0a08b1a0342783d': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'2c3e55a3334613b78acefa2edbfcf39a42235bcd': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	'199edbb016d523d3812eaa35cce8e5818408b5d0': { 'type': Rgh13BuildType.TILTSW, 'badjasper': True },
	# rgh13_jasper_extpwr.bin
	'f41c3308868eac84057e7a02dfe4c7a3907b9d66': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'f6c29ce441eec115df812bb1ee52f56c943f0922': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'a9de5d03fa3d6f17513a565175e56022cc9fc938': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'371c52279be5a243e455a7ed80f1c5c1fc41ffbc': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'a4f98aed88d59fd6abd8705e5dd309bde4c178e9': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'f97d69a3dabe66e4551bd2fee2b0099e35041521': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'f2fb4119cd3f58c85a608d998529dd79bf23862a': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'f6c29ce441eec115df812bb1ee52f56c943f0922': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'b67a9c26247c6da5754e8ee2fe2cd55f74ed3a6e': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'371c52279be5a243e455a7ed80f1c5c1fc41ffbc': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'723e10f78b2db487a1d667a0ae52e4b226daf894': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'a4e61a0a61ecd611223b0bd3d132aa4fe5aa08b2': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'6c34ab7403dd2c3a25d73d573815279fa5cac1a6': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'ea991eea575b2331131659c0b6879d2e27166acc': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'82e3295983da65480ac7029af56e38ab0e2f5c66': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'bcd7a2e107b4b7d0bb6c6442b2d2cad61ca7a45e': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	# rgh13_badjasper_extpwr.bin
	'5df8adb6afbf796072b2b312e96c4869aa92dd94': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'ccb061233592759a3cfd2710905428a3c35e3f74': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'71de94b29dc0eecc1dab71d3e2f6139bfb879d84': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'936f928d15b2f0117ba693a6ef81bad130a54470': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'9a2dad36f7ff1ec7b2564d08f780d605bb97b41c': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'ef1747aef0b05628341aa3b64b78b5ba5aa86f3c': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'be233094bac61672201ea8c416263a4141468ae4': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'd10e64ddd68e3b0a631ae683e5e60d00a25c0e50': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'5df8adb6afbf796072b2b312e96c4869aa92dd94': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'c46eb1370523101ca51be448ffbdc63fc3ab97d8': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'a0074dcec96a0f5875ada4963ce25513f954cccb': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'3204f57b74c6f5e9eba2b43984516c2cd9e453bb': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'67ba8910a96e59a76251e9f653a0997448a9ea0f': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'3c88e5b13f355eab7e33831094a10919ce68308a': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'be233094bac61672201ea8c416263a4141468ae4': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'c57b6f5f4576aaa36aa539851cd78b7f6c919726': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	# rgh13_jasper_for_falcon_extpwr.bin
	'032516aad3983b827b9d5f41c4202be1ab77b7cb': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'33bf65fd9ac4dbc6baef17c67ea1d8e6754f13a1': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'e111c308e29d1a3d9a1ff03887a720193c6ab9cf': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'5d3de7d2581163c649efd2e7ea4d0cac0f085f84': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'7b7d4c8b43631da69c6125324cbd3cafc651525a': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'86863ccb2ffed5f96baf8099df056d06b70b9022': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'fdc559e6cb511a9d8c4e8c934833b2b5909fc551': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'9002978a95f57473f0394d820a266a72396936e7': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'7b7d4c8b43631da69c6125324cbd3cafc651525a': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'01ce594f7f151787cef0335fdad8ffa36fb408db': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'9002978a95f57473f0394d820a266a72396936e7': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'4c92da2aebff506b74540fb57ced38252002db4e': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'a5f36af401b9a276e908303273dae308d93dfd82': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'8293cb4b48b53e1009e0774cf77c4c5d18facc3d': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'260cccb4a4bfb55418d27cdac60202279c997603': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'5dc04e0fd886d48d7972a0a4f37d63168902fd32': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	# rgh13_badjasper_for_falcon_extpwr.bin
	'de57171569423daa5ff5e4c7fa7f1ad0e5f86554': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'2dd2444994830c1ea8bed87cdde39bf379239b28': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'd9454b38cd78da03e552e07dd6930e3829c8668b': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'93f321c6b5daa6815e5f1f9947322af7fba1dc48': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'01427de32fbd06dbb9d5e59a67aec2a5f51475ed': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'bee72b97bd1f1fc8578ce55dd87dda51be8119ea': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'f39fd3249f49e216c11e541b5d71e489d0485197': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'964480ec602f589465be1ae5bd6ba96f898d6541': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'01427de32fbd06dbb9d5e59a67aec2a5f51475ed': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'5088c341ec774270b5ff5932b460bab0fa970522': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'c5fc3b5fbd2ccdfa160c91d265918a8d5a58d770': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'9af1497b583762eeef763a7d17172039cbf61c79': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'bee72b97bd1f1fc8578ce55dd87dda51be8119ea': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'c5a2367b30ff83c80c7b42da09f6c3ba24d5fdaa': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'e6da2d0d29eee03f799dc54b63b83bde7be37670': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'ea60ec970fd9563bdec0ae6a4c4829e1a6a9069c': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	# rgh13_jasper_for_zephyr_extpwr.bin
	'9002978a95f57473f0394d820a266a72396936e7': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'33bf65fd9ac4dbc6baef17c67ea1d8e6754f13a1': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'7b7d4c8b43631da69c6125324cbd3cafc651525a': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'86863ccb2ffed5f96baf8099df056d06b70b9022': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'8293cb4b48b53e1009e0774cf77c4c5d18facc3d': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'5dc04e0fd886d48d7972a0a4f37d63168902fd32': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'7b7d4c8b43631da69c6125324cbd3cafc651525a': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'a5f36af401b9a276e908303273dae308d93dfd82': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'032516aad3983b827b9d5f41c4202be1ab77b7cb': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	'9002978a95f57473f0394d820a266a72396936e7': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': False },
	# rgh13_badjasper_for_zephyr_extpwr.bin
	'01427de32fbd06dbb9d5e59a67aec2a5f51475ed': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'5088c341ec774270b5ff5932b460bab0fa970522': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'9af1497b583762eeef763a7d17172039cbf61c79': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'de57171569423daa5ff5e4c7fa7f1ad0e5f86554': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'2dd2444994830c1ea8bed87cdde39bf379239b28': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'01427de32fbd06dbb9d5e59a67aec2a5f51475ed': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'bee72b97bd1f1fc8578ce55dd87dda51be8119ea': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'ea60ec970fd9563bdec0ae6a4c4829e1a6a9069c': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'bee72b97bd1f1fc8578ce55dd87dda51be8119ea': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	'c5a2367b30ff83c80c7b42da09f6c3ba24d5fdaa': { 'type': Rgh13BuildType.EXTPWR, 'badjasper': True },
	# rgh13_jasper_chkstop.bin
	'6cc4cde86cace80834950610badbf8163104b43a': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'5b90be6862d7122627e7bf31fd1de21396de9328': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'b5715dd0eea1007938e7a2dd0bdff98fd501ceb6': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f1aa083c7362e958e1c4ae8be65402b115fb2f81': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'ee5d25a3e0d02a180d935b624b04ee2db56ad3d1': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'708e79b88bbffc4ccadd8b5114bd9e501d6f2e9d': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'64c04867c1d8541b4386b03c84c35eaf60836460': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'39cc3d2a006ff5fc070438a80f00db1f599f9ff1': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'f4c079be8f40f060596f68f78afd25055a07548f': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'82bd43a698add5bc314423436ab2ff36f52a7ac9': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'87668fb5c3c9ae20daae0f270449ed79a77a14e7': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'82bd43a698add5bc314423436ab2ff36f52a7ac9': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'b5715dd0eea1007938e7a2dd0bdff98fd501ceb6': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'8125436e2a418b76a21774b8b75cd8a124c628f4': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'26d586522f6bd4d8728625e500f302563edd85e5': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	# rgh13_badjasper_chkstop.bin
	'd3dfe3ac4809b0aa264f2646ce75aa55fa0a02ee': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'7add514fcc310818ee215b4243e793a655651648': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'e91bf50c94944e24626faf239408892e2cf6f8eb': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'56aff8490a44b01b8a9fa51e8b5500d086ffa2d4': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'21f5a346ef128c4ba85a7923c37818711de56405': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'40cc2d3dead26721cc519168268e5cb90b9d7848': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'5f6f0b4b9c5c88abdbc6d98c56e57f70f9ff18b1': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'7add514fcc310818ee215b4243e793a655651648': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'24575af50be970b6168978932aa7cec6ad2689df': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'4dd9b492a5d02c705eb14d5f955f72ce7a77b64e': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'7f2d0c4f3dc9ba33c3b7d58cbcf3131ac7356e79': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'08428b6521503e36956acf2e82a076c375aa108a': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'94a33d84df521c66abdfc92a3035956a5539adcd': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'5f6f0b4b9c5c88abdbc6d98c56e57f70f9ff18b1': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'c6ef5006afc4fc803c72d5e5e1e53e00f65e338b': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	# rgh13_jasper_for_falcon_chkstop.bin
	'09eb33f33bd89a7b233bf6b63338e3f59d5966c2': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'da11e21278c939d0427bc53dc161688939809ab2': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'6fbc10f4b5bb71b7c5ba12387be38c1f83674c90': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'a09ed585c80f2ca039b40d663d2ada6dd9c22773': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'4798470b625ab2e0e5a4c00b5f97df8800da4786': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'6fbc10f4b5bb71b7c5ba12387be38c1f83674c90': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'e35ffdbcb0d367697716eb7c906dc5dc79e7ca7d': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'884802fbfaa17e5208c2a3eb9b088893c57f5613': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'51947585e8eef8c9e6362b0107f6e59973afcef9': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'3449dbf8598912dd7b0f4da98c42daa229f2c18f': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'4625178355bbdbfd30a215fb90c347ebb5f5dbf6': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'9b3b10d6f4a86714840d25054ab40481934d8c2c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'3449dbf8598912dd7b0f4da98c42daa229f2c18f': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'733e1c890039f912c9dd99547a84910aacdb4602': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'4918edb3db93620b3c51dec9a4e5e6bbc022a758': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	# rgh13_badjasper_for_falcon_chkstop.bin
	'd33008956591aa0920dc69eae6381473221d061c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'b00bbb19947c30c7e24cf7d77b61827584764ad0': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'76215ce16b722fe6456ed53261673c75d6ad418d': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'b00bbb19947c30c7e24cf7d77b61827584764ad0': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'ac0fd620b04bec233bcfc33c5b1579d0edcbc7db': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'e7471822eb18d2a6140d015ee29e8a0721e9b93c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'37ec5fa9654f17736715b1e45d52af043c7c3acc': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'76215ce16b722fe6456ed53261673c75d6ad418d': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'249cfa14b6d7f1ea314618b82bcdaf1b2bf01bf3': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'c3da410c627b5bae263e5ce76d0ab0419ebebd2c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'4e29d040020deccb8bc7d3e8e0903279440dec15': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'5941f20168d66779ee7138223715fb27359c5f6e': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'fdc6a972df923ae043bed8e9e023281ff3cf2a46': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'f32f4f9159b2b3e9587139cbdb3799778f6a17bc': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'f6d9a273b10f74771e663abe32aa64f59a0e810a': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	# rgh13_jasper_for_zephyr_chkstop.bin
	'733e1c890039f912c9dd99547a84910aacdb4602': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'3449dbf8598912dd7b0f4da98c42daa229f2c18f': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'4918edb3db93620b3c51dec9a4e5e6bbc022a758': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'4625178355bbdbfd30a215fb90c347ebb5f5dbf6': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'51947585e8eef8c9e6362b0107f6e59973afcef9': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'3449dbf8598912dd7b0f4da98c42daa229f2c18f': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'6fbc10f4b5bb71b7c5ba12387be38c1f83674c90': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'a09ed585c80f2ca039b40d663d2ada6dd9c22773': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'6fbc10f4b5bb71b7c5ba12387be38c1f83674c90': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	'09eb33f33bd89a7b233bf6b63338e3f59d5966c2': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': False },
	# rgh13_badjasper_for_zephyr_chkstop.bin
	'4e29d040020deccb8bc7d3e8e0903279440dec15': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'76215ce16b722fe6456ed53261673c75d6ad418d': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'37ec5fa9654f17736715b1e45d52af043c7c3acc': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'e7471822eb18d2a6140d015ee29e8a0721e9b93c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'ac0fd620b04bec233bcfc33c5b1579d0edcbc7db': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'b00bbb19947c30c7e24cf7d77b61827584764ad0': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'76215ce16b722fe6456ed53261673c75d6ad418d': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'd33008956591aa0920dc69eae6381473221d061c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'c3da410c627b5bae263e5ce76d0ab0419ebebd2c': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	'b00bbb19947c30c7e24cf7d77b61827584764ad0': { 'type': Rgh13BuildType.TWO_WIRE_CHKSTOP, 'badjasper': True },
	# rgh13_jasper_1wire.bin
	'dab772633b0154dbe2545dde945d755bfa830d9a': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'2b34f82f4744297e98093cc6402200bd9fd55d8e': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f4cdf687c60ba5efb916edf5a611d01164d6ad1b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'e890689938a2c0ab9c44a6cf8f38d4eaf20cd9bb': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'b103dacf11b60176598e30cd79d06552a0a308a0': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'a9ecffea804d09700c0ef103a141b24f5a37aeca': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'0df53b8f04c3e81074852b6fbd1c95fb28d20c43': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'a801d5daf2f6a847770b5c0fa631860eaeb67594': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'7db12a3b761bcccfca3e2b39178fe953e6b0b508': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'dab772633b0154dbe2545dde945d755bfa830d9a': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f09c297fd5de5f0549bffc9604d8c8f5e2d178f1': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'7018d0350a1dd1e47d5b0439dfacf4a951bfcb42': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'245c181aae93001c561400238c62df723715c239': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'245c181aae93001c561400238c62df723715c239': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	# rgh13_badjasper_1wire.bin
	'8fcd7026094c7da903f9507cf52339965287b8b8': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'1c2a51cfffdb2d26ab721fdf41d56b733166eb6e': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'adc4ff228671ebc41af61f11784b3927922f3f8f': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'78a50794e86c3649a1e3643eaddcd054b0ddd21b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'dfa3aaa08c2bff2eda5e9a76e8b89f4e6f8905a3': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'7c7b99f006c3da10c6bc4aa2defc84a9d2691f64': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'd046e1da43db3d10b930e7b85b12961207c576cc': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'34b2324dc5bf1be03f8e574e5214a8b4a9f2ee31': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'd2ad76550870156fe9d57c197747f01ea77c27ef': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'8fcd7026094c7da903f9507cf52339965287b8b8': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'cd9e12da4ef85e64721cc8466796b4a1c6c3a92b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'cd9e12da4ef85e64721cc8466796b4a1c6c3a92b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	# rgh13_jasper_for_falcon_1wire.bin
	'dab772633b0154dbe2545dde945d755bfa830d9a': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'7018d0350a1dd1e47d5b0439dfacf4a951bfcb42': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'0df53b8f04c3e81074852b6fbd1c95fb28d20c43': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'b103dacf11b60176598e30cd79d06552a0a308a0': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'a9ecffea804d09700c0ef103a141b24f5a37aeca': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'245c181aae93001c561400238c62df723715c239': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'245c181aae93001c561400238c62df723715c239': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'a801d5daf2f6a847770b5c0fa631860eaeb67594': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'2b34f82f4744297e98093cc6402200bd9fd55d8e': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'dab772633b0154dbe2545dde945d755bfa830d9a': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f4cdf687c60ba5efb916edf5a611d01164d6ad1b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'7db12a3b761bcccfca3e2b39178fe953e6b0b508': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f09c297fd5de5f0549bffc9604d8c8f5e2d178f1': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'e890689938a2c0ab9c44a6cf8f38d4eaf20cd9bb': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	# rgh13_badjasper_for_falcon_1wire.bin
	'd046e1da43db3d10b930e7b85b12961207c576cc': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'78a50794e86c3649a1e3643eaddcd054b0ddd21b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'cd9e12da4ef85e64721cc8466796b4a1c6c3a92b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'adc4ff228671ebc41af61f11784b3927922f3f8f': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'7c7b99f006c3da10c6bc4aa2defc84a9d2691f64': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'1c2a51cfffdb2d26ab721fdf41d56b733166eb6e': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'34b2324dc5bf1be03f8e574e5214a8b4a9f2ee31': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'd2ad76550870156fe9d57c197747f01ea77c27ef': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'dfa3aaa08c2bff2eda5e9a76e8b89f4e6f8905a3': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'8fcd7026094c7da903f9507cf52339965287b8b8': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'8fcd7026094c7da903f9507cf52339965287b8b8': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'cd9e12da4ef85e64721cc8466796b4a1c6c3a92b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	# rgh13_jasper_for_zephyr_1wire.bin
	'0df53b8f04c3e81074852b6fbd1c95fb28d20c43': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'dab772633b0154dbe2545dde945d755bfa830d9a': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'e890689938a2c0ab9c44a6cf8f38d4eaf20cd9bb': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f4cdf687c60ba5efb916edf5a611d01164d6ad1b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'f09c297fd5de5f0549bffc9604d8c8f5e2d178f1': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'dab772633b0154dbe2545dde945d755bfa830d9a': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'b103dacf11b60176598e30cd79d06552a0a308a0': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'245c181aae93001c561400238c62df723715c239': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'245c181aae93001c561400238c62df723715c239': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	'a9ecffea804d09700c0ef103a141b24f5a37aeca': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': False },
	# rgh13_badjasper_for_zephyr_1wire.bin
	'cd9e12da4ef85e64721cc8466796b4a1c6c3a92b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'd046e1da43db3d10b930e7b85b12961207c576cc': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'8fcd7026094c7da903f9507cf52339965287b8b8': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'8fcd7026094c7da903f9507cf52339965287b8b8': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'dfa3aaa08c2bff2eda5e9a76e8b89f4e6f8905a3': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'cd9e12da4ef85e64721cc8466796b4a1c6c3a92b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'd2ad76550870156fe9d57c197747f01ea77c27ef': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'78a50794e86c3649a1e3643eaddcd054b0ddd21b': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'7c7b99f006c3da10c6bc4aa2defc84a9d2691f64': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	'1c2a51cfffdb2d26ab721fdf41d56b733166eb6e': { 'type': Rgh13BuildType.ONE_WIRE, 'badjasper': True },
	# rgh13_jasper_0wire.bin
	'2ce29de6207fe82d83dd2ec4cba1df14c198e51a': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'78be06a67f5df94e85bca7fd9a5a560c57df9e3a': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'af3e5d6e35b44ec2a8ad5de599f0df4b5804dee1': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'81a9a7bd2ebca91ec06f8682a2f7f405e71560a3': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'4ce4caa954d82e47f9d884a7ff0643160b7a4c15': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'9ae408ba47c7c4cbc19473f9b36db50ac000b212': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'0b11a161f2bd4ee8f875b462d66f2c9acd5dba0d': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'3d2796de78e3cab78f3ba7bb466c5aac2d29127f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'c33555a0c22b35b614eaf9c110bde5a5cec7f071': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'08ee9a8115020c19dac29ca311afc20bf424c77f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'39e4a65e19938fc376910c5b4ad1920cd4700b84': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'655c030d91900f4e1e09b34e20bf5ecaf76ca6a0': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'81a9a7bd2ebca91ec06f8682a2f7f405e71560a3': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'a9418f27cf37cb264507a8b75e5d6e41f4365b5f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'a9418f27cf37cb264507a8b75e5d6e41f4365b5f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	# rgh13_badjasper_0wire.bin
	'80469d9ae0c4ad5308d0889cb4ff820600489626': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'10a666d9fdebfd82f5df915f2322df40b0ac9f68': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'5caabcc7118be5051af267139185b2a7c8df8540': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'3f7abb49d751ba9cdc09c366a44258dd5b104151': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'6b836791e9f6753159622a1ef96dfe84c2db3a78': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'653febccd00a8cd59229a622cf0b346ac11ecd76': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'd6aa8b292057f303ee96dfc26f23f82e3cc7d230': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'756877786347105de7fd1006a40b7a2bbd41310c': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'80c1b37c0948ceaeaec81b22d3bf57ca2ab5816b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'80c1b37c0948ceaeaec81b22d3bf57ca2ab5816b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'd33f8edbcc971ffb452bbb310905b1892337d7fa': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'52d833ff8dca2019e959a5877cd116d89e2f9bd0': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'3f7abb49d751ba9cdc09c366a44258dd5b104151': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	# rgh13_jasper_for_falcon_0wire.bin
	'08ee9a8115020c19dac29ca311afc20bf424c77f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'78be06a67f5df94e85bca7fd9a5a560c57df9e3a': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'9ae408ba47c7c4cbc19473f9b36db50ac000b212': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'81a9a7bd2ebca91ec06f8682a2f7f405e71560a3': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'39e4a65e19938fc376910c5b4ad1920cd4700b84': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'81a9a7bd2ebca91ec06f8682a2f7f405e71560a3': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'0b11a161f2bd4ee8f875b462d66f2c9acd5dba0d': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'4ce4caa954d82e47f9d884a7ff0643160b7a4c15': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'a9418f27cf37cb264507a8b75e5d6e41f4365b5f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'a9418f27cf37cb264507a8b75e5d6e41f4365b5f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'c33555a0c22b35b614eaf9c110bde5a5cec7f071': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'2ce29de6207fe82d83dd2ec4cba1df14c198e51a': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'3d2796de78e3cab78f3ba7bb466c5aac2d29127f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'655c030d91900f4e1e09b34e20bf5ecaf76ca6a0': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'af3e5d6e35b44ec2a8ad5de599f0df4b5804dee1': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	# rgh13_badjasper_for_falcon_0wire.bin
	'80469d9ae0c4ad5308d0889cb4ff820600489626': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'd6aa8b292057f303ee96dfc26f23f82e3cc7d230': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'10a666d9fdebfd82f5df915f2322df40b0ac9f68': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'd33f8edbcc971ffb452bbb310905b1892337d7fa': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'80c1b37c0948ceaeaec81b22d3bf57ca2ab5816b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'52d833ff8dca2019e959a5877cd116d89e2f9bd0': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'5caabcc7118be5051af267139185b2a7c8df8540': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'756877786347105de7fd1006a40b7a2bbd41310c': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'80c1b37c0948ceaeaec81b22d3bf57ca2ab5816b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'653febccd00a8cd59229a622cf0b346ac11ecd76': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'6b836791e9f6753159622a1ef96dfe84c2db3a78': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'3f7abb49d751ba9cdc09c366a44258dd5b104151': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'3f7abb49d751ba9cdc09c366a44258dd5b104151': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	# rgh13_jasper_for_zephyr_0wire.bin
	'81a9a7bd2ebca91ec06f8682a2f7f405e71560a3': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'9ae408ba47c7c4cbc19473f9b36db50ac000b212': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'655c030d91900f4e1e09b34e20bf5ecaf76ca6a0': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'af3e5d6e35b44ec2a8ad5de599f0df4b5804dee1': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'3d2796de78e3cab78f3ba7bb466c5aac2d29127f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'a9418f27cf37cb264507a8b75e5d6e41f4365b5f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'a9418f27cf37cb264507a8b75e5d6e41f4365b5f': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'4ce4caa954d82e47f9d884a7ff0643160b7a4c15': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'c33555a0c22b35b614eaf9c110bde5a5cec7f071': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	'81a9a7bd2ebca91ec06f8682a2f7f405e71560a3': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': False },
	# rgh13_badjasper_for_zephyr_0wire.bin
	'80c1b37c0948ceaeaec81b22d3bf57ca2ab5816b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'd6aa8b292057f303ee96dfc26f23f82e3cc7d230': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'80c1b37c0948ceaeaec81b22d3bf57ca2ab5816b': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'3f7abb49d751ba9cdc09c366a44258dd5b104151': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'3f7abb49d751ba9cdc09c366a44258dd5b104151': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'6b836791e9f6753159622a1ef96dfe84c2db3a78': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'5caabcc7118be5051af267139185b2a7c8df8540': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'80469d9ae0c4ad5308d0889cb4ff820600489626': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'756877786347105de7fd1006a40b7a2bbd41310c': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
	'52d833ff8dca2019e959a5877cd116d89e2f9bd0': { 'type': Rgh13BuildType.ZERO_WIRE, 'badjasper': True },
}

def _rgh13_try_fingerprint(smcbin: bytes):
    hashed = hashlib.sha1(smcbin[0x2C00:0x2FE0]).hexdigest()
    return OLD_SMC_FINGERPRINTS[hashed]

def _rgh13_watermark_is_valid(smcbin: bytes):
    checksum = 0
    for i in range(0x2FE8,0x2FEF):
        checksum += smcbin[i]
    return (checksum & 0xFF) == smcbin[0x2FEF]

def main():
    if len(sys.argv) < 2:
        print("error: need to specify path to nand")
        return None
    
    flash_path = sys.argv[1]

    nand = None
    with open(flash_path, "rb") as f:
        f.seek(0, os.SEEK_END)
        nand_size = f.tell()
        f.seek(0, os.SEEK_SET)

        if (nand_size % 0x4200) != 0:
            print("error: nand size invalid, probably not a valid ECC image")
            return

        nand = f.read()

    nand_type = ecc.ecc_detect_type(nand)
    if nand_type is None:
        print("NAND type cannot be detected, exiting.")
        return
    
    if nand_type == ecc.NandType.NAND_64M:
        print("found Jasper big boy NAND")

    if nand_type == ecc.NandType.NAND_16M_JASPER:
        print("found Jasper-style 16m NAND")

    if nand_type == ecc.NandType.NAND_16M:
        print("found standard 16m NAND")

    nand_stripped = ecc.ecc_strip(nand[0:0x021000 * 4])

    # CB_X must be present
    loaders = _extract_loaders(nand_stripped)
    if 'cbx' not in loaders:
        print("not a glitch3 rgh3/rgh1.3 style image")
        return

    smc_plaintext = smc.decrypt_smc(nand_stripped[0x1000:0x4000])
    if smc.smc_ident(smc_plaintext) is None:
        print("SMC image is bad")
        return None
    
    if smc_plaintext[0x2FE8] == 0x13 and smc_plaintext[0x2FEE] == 0x31 and \
        _rgh13_watermark_is_valid(smc_plaintext):
        print("found RGH1.3 SMC watermark, and it's valid...")
        print(f"\tPOST wiring type: {Rgh13BuildType(smc_plaintext[0x2FE9])}")
        print(f"\tbadjasper: {smc_plaintext[0x2FEA] != 0}")
        return
    
    print("watermark not found, falling back on hash match...")
    entry = _rgh13_try_fingerprint(smc_plaintext)
    if entry is not None:
        print("SMC matched one of our known historical builds")
        print(f"\tPOST wiring type: {entry['type']}")
        print(f"\tbadjasper: {entry['badjasper']}")
        return
    
    print("unable to identify build type")

if __name__ == '__main__':
    main()
