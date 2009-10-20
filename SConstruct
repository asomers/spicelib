# vim: filetype=python :
# vim: sw=4 :
# vim: ts=4 :

#HOW TO ADD VENDORS
#
#Inherit from Vendor
#Define these attributes
#   abbrev: short abbreviation for your vendor's name
#   download_urls: url(s) for the primary file(s) that need downloading
#   sections:   list of sections for which we are preparing files
#           valid sections are 'diodes', 'bipolar', 'opamps', etc
#   unpack_by_section: True if your files unpack by category
#           e.g. bipolar, opamps, etc
#Define these methods
#   unpack_<section>: define for all sections present
#   <section>_fixups: define for all sections present.  This method determines
#           what fixes and patches need to be applied for which model
#If neccessary, overload any methods of Vendor
#New fixups, if needed, should be added to scripts/fixups.py as coroutines
#New fixups are preferable to new patches


import os
import popen2
import sys
import re
import anydbm

sys.path.append('scripts')
import testlibrary
import fix_name_has_slash
import fixups

TEMPDIR='unpack'
MODEL_SIGDIR='model_checksums'
MODEL_LIBDIR='model_library'
TESTDIR='model_tests'
PATCHDIR='model_patches'


env = Environment(ENV = {'PATH': os.environ["PATH"]})
SConsignFile('.sconsign.dbm', anydbm)

#Custom builders
def test_single(target, source, env):
    #target should be the status.htm file
    #source should be all dependent files
    #env.library should be a testlibrary.modellibrary
    #env.partid should be the section from the index file eg LM741_LM0001
    partid = env.partid
    env.library.test_single(partid)
    return None
bld = Builder(action = test_single)
env.Append(BUILDERS = {'TestSingle': bld})

def html_index(target, source, env):
    """Build the test index html file.  source is the parts.index file followed
    by every TestSingle node on which it depends"""
    filename = str(source[0])
    library = testlibrary.modellibrary(filename)
    library.htmlindex()
    return None
bld = Builder(action = html_index)
env.Append(BUILDERS = {'HtmlIndex': bld})


#Make necessary directories
if not os.path.isdir(MODEL_SIGDIR):
    Execute(Mkdir(MODEL_SIGDIR))


def mk_aliases(*args):
    for phase in ['download', 'unpack', 'create', 'test']:
        env.Alias(phase, [phase + '_' + arg.abbrev for arg in args])


class Vendor(object):
    def __init__(self):
        self.download_all_node = self.download_all()
        env.Alias('download_' + self.abbrev, self.download_all_node)
        self.unpack_all_nodes = self.unpack_all()
        env.Alias('unpack_' + self.abbrev, self.unpack_all_nodes)
        self.create_all_nodes = self.create_all()
        env.Alias('create_' + self.abbrev, self.create_all_nodes)
        self.test_all_nodes = self.test_all()
        self.test_index_all_nodes = self.test_index_all()
        env.Alias('test_' + self.abbrev, self.test_index_all_nodes)
    def download_all(self):
        basedir = os.path.join('downloads', self.abbrev)
        nodes = []
        for url in self.download_urls:
            file = url.split('/')[-1]
            checksum_file = os.path.join(MODEL_SIGDIR, 
                                         self.abbrev + '_all.md5sum')
            nodes.append(env.Command(os.path.join(basedir, file), None, 
                """
                wget -N -P `dirname $TARGET` %s
                md5sum $TARGET > %s
                """
                % (url, checksum_file)))
        return nodes
    def unpack_all(self):
        nodes = []
        dir_ = os.path.join(TEMPDIR, self.abbrev)
        if not os.path.isdir(dir_):
            Execute(Mkdir(dir_))
        for sec in self.sections:
            nodes.append(getattr(self, 'unpack_' + sec)())
        return nodes
    def create_all(self):
        nodes = []
        for sec in self.sections:
            node = self.create_section(sec)
            env.Alias('create_' + self.abbrev + '_' + sec, node)
            nodes.append(node)
        return nodes
    def create_section(self, section):
        nodes = []
        if self.unpack_by_section:
            unpack_dir = os.path.join(TEMPDIR, self.abbrev, section)
        else:
            unpack_dir = os.path.join(TEMPDIR, self.abbrev)
        create_dir = os.path.join(MODEL_LIBDIR, self.abbrev, section)
        csfile = os.path.join(MODEL_SIGDIR, self.abbrev + '_' + section + '_lib.md5sum')
        if not os.path.isdir(create_dir):
            Execute(Mkdir(create_dir))
        targets = set([])
        for root, dirs, files in os.walk(unpack_dir):
            try:
                reldir = os.path.join(*(root.split(os.sep)[2:]))
            except TypeError:
                reldir = '.'
            for model in files:
                flist, patch = getattr(self, section + '_fixups')(model, reldir)
                if flist != None and model not in targets:
                    source = os.path.join(root, model)
                    target = os.path.join(create_dir, model)
                    envtemp = env.Clone()
                    envtemp.flist = flist
                    def builder(target, source, env):
                        read = fixups.read(source[0])
                        fixups.write(target[0], reduce(lambda x, y: y(x), env.flist, read))
                    node = envtemp.Command(target, source, builder)
                    targets.add(model)
                    AddPostAction(target, 'md5sum $TARGET >> %s' % csfile)
                    if patch != None:
                        AddPostAction(target, 'patch -d %s -p1 < %s' % (create_dir, os.path.join(PATCHDIR, patch)))
                    nodes.append(node)
        return nodes
    def test_all(self):
        nodes = []
        for sec in self.sections:
            nodes.append(self.test_section(sec))
        return nodes
    def test_section(self, section):
        nodes = []
        indexfile = os.path.join('indexfiles', 
                                 ''.join([self.abbrev, '_', section, '.index']))
        library = testlibrary.modellibrary(indexfile)
        for name in library.modelparts:
            ignore_status = ['undefined', 'new']
            partid = name
            status = library.modelparts[partid].properties['model_status']
            if status in ignore_status:
                continue
            file = library.modelparts[partid].properties['file']
            sources = [indexfile,
                os.path.join(MODEL_LIBDIR, self.abbrev, section, file)]
            dir_ = os.path.join(TESTDIR, self.abbrev, section, partid)
            target = os.path.join(dir_, 'status.htm')
            tempenv = env.Clone()
            tempenv.partid = partid
            tempenv.library = library
            nodes.append(tempenv.TestSingle(target, sources))
        setattr(self, 'test_' + section, 
                env.Alias(''.join(['test_', self.abbrev, '_', section]), nodes))
        return nodes
    def test_index_all(self):
        nodes = []
        for sec in self.sections:
            nodes.append(self.test_index_section(sec))
        return nodes
    def test_index_section(self, section):
        return env.HtmlIndex(os.path.join(TESTDIR, self.abbrev, section, 'index.html'),
            [os.path.join('indexfiles', 
                ''.join([self.abbrev, '_', section, '.index'])),
             getattr(self, ''.join(['test_', section]))])



class LinearTechnology(Vendor):
    abbrev = 'ltc'
    unpack_by_section = False
    download_urls = ['http://ltspice.linear.com/software/LTC.zip']
    sections = ['opamps']
    all_ltc_opamps = [  #{{{1
    'LT1001.MOD', 'LT1002.MOD', 'LT1006.MOD', 'LT1007.MOD', 'LT1008.MOD',
    'LT1010.MOD', 'LT1012.MOD', 'LT1013.MOD', 'LT1014.MOD', 'LT1022.MOD',
    'LT1024.MOD', 'LT1028.MOD', 'LT1037.MOD', 'LT1055.MOD', 'LT1056.MOD',
    'LT1057.MOD', 'LT1058.MOD', 'LT1077.MOD', 'LT1078.MOD', 'LT1079.MOD',
    'LT1097.MOD', 'LT1101.MOD', 'LT1102.MOD', 'LT1112.MOD', 'LT1113.MOD',
    'LT1114.MOD', 'LT1115.MOD', 'LT1122.MOD', 'LT1124.MOD', 'LT1125.MOD',
    'LT1126.MOD', 'LT1127.MOD', 'LT1128.MOD', 'LT1167.MOD', 'LT1168.MOD',
    'LT1169.MOD', 'LT1178.MOD', 'LT1179.MOD', 'LT1187.MOD', 'LT1189.MOD',
    'LT1190.MOD', 'LT1191.MOD', 'LT1192.MOD', 'LT1193.MOD', 'LT1194.MOD',
    'LT1195.MOD', 'LT1203.MOD', 'LT1204.MOD', 'LT1205.MOD', 'LT1206.MOD',
    'LT1207.MOD', 'LT1208.MOD', 'LT1209.MOD', 'LT1210.MOD', 'LT1211.MOD',
    'LT1212.MOD', 'LT1213.MOD', 'LT1214.MOD', 'LT1215.MOD', 'LT1216.MOD',
    'LT1217.MOD', 'LT1218.MOD', 'LT1218L.MOD', 'LT1219.MOD', 'LT1219L.MOD',
    'LT1220.MOD', 'LT1221.MOD', 'LT1222.MOD', 'LT1223.MOD', 'LT1224.MOD',
    'LT1225.MOD', 'LT1226.MOD', 'LT1227.MOD', 'LT1228.MOD', 'LT1229.MOD',
    'LT1230.MOD', 'LT1251.MOD', 'LT1252.MOD', 'LT1253.MOD', 'LT1254.MOD',
    'LT1256.MOD', 'LT1259.MOD', 'LT1260.MOD', 'LT1351.MOD', 'LT1352.MOD',
    'LT1353.MOD', 'LT1354.MOD', 'LT1355.MOD', 'LT1356.MOD', 'LT1357.MOD',
    'LT1358.MOD', 'LT1359.MOD', 'LT1360.MOD', 'LT1361.MOD', 'LT1362.MOD',
    'LT1363.MOD', 'LT1364.MOD', 'LT1365.MOD', 'LT1366.MOD', 'LT1367.MOD',
    'LT1368.MOD', 'LT1369.MOD', 'LT1395.MOD', 'LT1396.MOD', 'LT1397.MOD',
    'LT1398.MOD', 'LT1399.MOD', 'LT1399HV.MOD', 'LT1413.MOD', 'LT1457.MOD',
    'LT1462.MOD', 'LT1463.MOD', 'LT1464.MOD', 'LT1465.MOD', 'LT1466L.MOD',
    'LT1467L.MOD', 'LT1468.MOD', 'LT1468-2.MOD', 'LT1469.MOD', 'LT1469-2.MOD',
    'LT1490A.MOD', 'LT1491A.MOD', 'LT1492.MOD', 'LT1493.MOD', 'LT1494.MOD',
    'LT1495.MOD', 'LT1496.MOD', 'LT1497.MOD', 'LT1498.MOD', 'LT1499.MOD',
    'LT1630.MOD', 'LT1631.MOD', 'LT1632.MOD', 'LT1633.MOD', 'LT1635.MOD',
    'LT1636.MOD', 'LT1637.MOD', 'LT1638.MOD', 'LT1639.MOD', 'LT1672.MOD',
    'LT1673.MOD', 'LT1674.MOD', 'LT1675.MOD', 'LT1675-1.MOD', 'LT1677.MOD',
    'LT1678.MOD', 'LT1679.MOD', 'LT1722.MOD', 'LT1723.MOD', 'LT1724.MOD',
    'LT1739.MOD', 'LT1782.MOD', 'LT1783.MOD', 'LT1784.MOD', 'LT1787.MOD',
    'LT1787HV.MOD', 'LT1789-1.MOD', 'LT1789-10.MOD', 'LT1792.MOD', 'LT1793.MOD',
    'LT1794.MOD', 'LT1795.MOD', 'LT1797.MOD', 'LT1800.MOD', 'LT1801.MOD',
    'LT1802.MOD', 'LT1803.MOD', 'LT1804.MOD', 'LT1805.MOD', 'LT1806.MOD',
    'LT1807.MOD', 'LT1809.MOD', 'LT1810.MOD', 'LT1812.MOD', 'LT1813.MOD',
    'LT1813HV.MOD', 'LT1814.MOD', 'LT1815.MOD', 'LT1816.MOD', 'LT1817.MOD',
    'LT1818.MOD', 'LT1819.MOD', 'LT1880.MOD', 'LT1881.MOD', 'LT1882.MOD',
    'LT1884.MOD', 'LT1885.MOD', 'LT1886.MOD', 'LT1920.MOD', 'LT1969.MOD',
    'LT1970.MOD', 'LT1990.MOD', 'LT1991.MOD', 'LT1993-10.MOD', 'LT1993-2.MOD',
    'LT1993-4.MOD', 'LT1994.MOD', 'LT1995.MOD', 'LT1996.MOD', 'LT2078.MOD',
    'LT2079.MOD', 'LT2178.MOD', 'LT2179.MOD', 'LT5514.MOD', 'LT5524.MOD',
    'LT5554.MOD', 'LT6000.MOD', 'LT6001.MOD', 'LT6002.MOD', 'LT6003.MOD',
    'LT6004.MOD', 'LT6005.MOD', 'LT6010.MOD', 'LT6011.MOD', 'LT6012.MOD',
    'LT6013.MOD', 'LT6014.MOD', 'LT6100.MOD', 'LT6106.MOD', 'LT6107.MOD',
    'LT6200.MOD', 'LT6200-10.MOD', 'LT6200-5.MOD', 'LT6201.MOD', 'LT6202.MOD',
    'LT6203.MOD', 'LT6204.MOD', 'LT6205.MOD', 'LT6206.MOD', 'LT6207.MOD',
    'LT6210.MOD', 'LT6211.MOD', 'LT6220.MOD', 'LT6221.MOD', 'LT6222.MOD',
    'LT6230.MOD', 'LT6230-10.MOD', 'LT6231.MOD', 'LT6232.MOD', 'LT6233.MOD',
    'LT6233-10.MOD', 'LT6234.MOD', 'LT6235.MOD', 'LT6300.MOD', 'LT6301.MOD',
    'LT6402-12.MOD', 'LT6402-20.MOD', 'LT6402-6.MOD', 'LT6411.MOD', 'LT6550.MOD',
    'LT6551.MOD', 'LT6552.MOD', 'LT6553.MOD', 'LT6554.MOD', 'LT6555.MOD',
    'LT6556.MOD', 'LT6557.MOD', 'LT6558.MOD', 'LT6559.MOD', 'LT6600-10.MOD',
    'LT6600-15.MOD', 'LT6600-2.5.MOD', 'LT6600-20.MOD', 'LT6600-5.MOD',
    'LT6604-10.MOD', 'LT6604-15.MOD', 'LT6604-2.5.MOD', 'LT6604-5.MOD',
    'LTC1047.MOD', 'LTC1049.MOD', 'LTC1050.MOD', 'LTC1051.MOD', 'LTC1052.MOD',
    'LTC1053.MOD', 'LTC1100.MOD', 'LTC1150.MOD', 'LTC1151.MOD', 'LTC1152.MOD',
    'LTC1250.MOD', 'LTC1541.MOD', 'LTC1542.MOD', 'LTC1564.MOD', 'LTC1992.MOD',
    'LTC2050.MOD', 'LTC2050HV.MOD', 'LTC2051.MOD', 'LTC2051HV.MOD', 'LTC2052.MOD',
    'LTC2052HV.MOD', 'LTC2053.MOD', 'LTC2053-SYNC.MOD', 'LTC2054.MOD',
    'LTC2054HV.MOD', 'LTC2055.MOD', 'LTC2055HV.MOD', 'LTC4151.MOD', 'LTC6078.MOD',
    'LTC6079.MOD', 'LTC6081.MOD', 'LTC6082.MOD', 'LTC6084.MOD', 'LTC6085.MOD',
    'LTC6087.MOD', 'LTC6088.MOD', 'LTC6101.MOD', 'LTC6101HV.MOD', 'LTC6102.MOD',
    'LTC6102HV.MOD', 'LTC6103.MOD', 'LTC6104.MOD', 'LTC6240.MOD', 'LTC6240HV.MOD',
    'LTC6241.MOD', 'LTC6241HV.MOD', 'LTC6242.MOD', 'LTC6242HV.MOD', 'LTC6244.MOD',
    'LTC6244HV.MOD', 'LTC6400-14.MOD', 'LTC6400-20.MOD', 'LTC6400-26.MOD',
    'LTC6400-8.MOD', 'LTC6401-14.MOD', 'LTC6401-20.MOD', '.MOD', 'LTC6401-26.MOD',
    'LTC6401-8.MOD', 'LTC6403-1.MOD', 'LTC6404-1.MOD', 'LTC6404-2.MOD',
    'LTC6404-4.MOD', 'LTC6405.MOD', 'LTC6406.MOD', 'LTC6410-6.MOD', 'LTC6412.MOD',
    'LTC6416.MOD', 'LTC6420-20.MOD', 'LTC6421-20.MOD', 'LTC6601-1.MOD',
    'LTC6601-2.MOD', 'LTC6602.MOD', 'LTC6603.MOD', 'LTC6605-10.MOD',
    'LTC6605-14.MOD', 'LTC6605-7.MOD', 'LTC6800.MOD', 'LTC6910-1.MOD',
    'LTC6910-2.MOD', 'LTC6910-3.MOD', 'LTC6911-1.MOD', 'LTC6911-2.MOD',
    'LTC6912-1.MOD', 'LTC6912-2.MOD', 'LTC6915.MOD']    #}}}
    def unpack_opamps(self):
        return env.Command(None, self.download_all_node,
            """
            unzip -o -d %(TEMPDIR)s $SOURCE
            scripts/ltcsplit.py -d %(TEMPDIR)s %(TEMPDIR)s/LTC.lib
            """ % { 'TEMPDIR': os.path.join(TEMPDIR, 'ltc')})
    def opamps_fixups(self, modelname, dir):
        patch = None
        fixes = []
        if not modelname in self.all_ltc_opamps:
            return None, None
        else:
            return fixes, None


class TexasInstruments(Vendor):
    abbrev = 'ti'
    unpack_by_section = False
    download_urls = [
        'http://focus.ti.com/packaged_lits/pspice_files/ti_pspice_models.zip',
        'http://focus.ti.com/packaged_lits/pspice_files/ti_pspice_models_index.txt']
    sections = ['opamps']
    def unpack_opamps(self):
        return env.Command(None, self.download_all_node,
            """
            unzip -o -d %(TEMPDIR)s $SOURCE
            find %(TEMPDIR)s -type f -exec md5sum {} \; | \
                sort -k 2 >>%(SIGFILE)s
            find %(TEMPDIR)s -name '*.zip' -exec unzip -o -d {}_d {} \;
            """ % {'TEMPDIR': os.path.join(TEMPDIR, 'ti'),
                   'SIGFILE': os.path.join(MODEL_SIGDIR, 'ti_all.md5sum')})
    def opamps_fixups(self, model, dir):
        #TODO: create ti opamps based on ti_pspice_models_index.txt
        firstdir = dir.split(os.sep)[1]
        if 'opa' != firstdir[0:3] or \
                os.path.splitext(model)[1] not in \
                    ['.mod', '.MOD', '.txt', '.sub'] or \
                model in ['Readme.txt', 'disclaimer.txt']:
            return None, None
        else:
            return [], None


class NationalSemiconductor(Vendor):
    abbrev = 'national'
    unpack_by_section = True
    download_urls = ['http://www.national.com/analog/amplifiers/spice_models']
    sections = ['opamps']
    def download_all(self):
        url = self.download_urls[0]
        basedir = os.path.join('downloads', self.abbrev)
        file = os.path.join(basedir, url.split('/')[-1])
        csfile = os.path.join(MODEL_SIGDIR, self.abbrev + '_all.md5sum')
        #Really, this command has many more targets than just the initial
        #download.  However, they are not known until the initial download
        #has happened.  The downside to this is that if a target file 
        #dissapears, scons won't know to redownload it
        node = env.Command(file, None,
            """
            wget -N -P `dirname %(file)s` %(url)s
            md5sum %(file)s > %(csfile)s
            wget -N -P %(ddir)s `awk -F '"' '/href.*javascript.*href.*\.MOD/ {print $6; next} /href.*\.MOD/ {print $4}' %(file)s | sort | uniq`
            """ % {'ddir' : os.path.join(basedir, 'opamps'),
                'file': file, 'url': url, 'csfile': csfile})
        return node
    def unpack_opamps(self):
        #Really, this command has many more targets than just LM741.MOD
        #However, they are not known until the initial download
        #has happened.  The downside to this is that if a target file 
        #dissapears, scons won't know to rebuild it
        example_target = os.path.join(TEMPDIR, 'national', 'opamps', 'LM741.MOD')
        return env.Command(example_target, self.download_all_node,
            """
            md5sum downloads/national/opamps/*.MOD > %(sigfile)s
            cp downloads/national/opamps/*.MOD %(tempdir)s
            md5sum downloads/national/opamps/*.MOD >> %(sigfile)s
            """ % 
            {'sigfile': os.path.join(MODEL_SIGDIR, 'national_opamps.md5sum'),
             'tempdir': os.path.join(TEMPDIR, 'national', 'opamps')})
    def opamps_fixups(self, modelname, dir):
        string_replacements = {
                'LMH6619.MOD': ('LMH6618', 'LMH6619'),
                'LMP7702.MOD': ('LMP7701', 'LMP7702'),
                'LMP7704.MOD': ('LMP7701', 'LMP7704'),
                'LMP7709.MOD': ('LMP7707', 'LMP7709'),
                'LMP7712.MOD': ('LMP7711', 'LMP7712'),
                'LMV552.MOD': ('LMV551', 'LMV552'),
                'LMV652.MOD': ('LMV651', 'LMV652')
                }
        patch = None
        fixes = []
        if modelname in string_replacements:
            query, repl = string_replacements[modelname]
            def f(gen):
                return fixups.replace_string(query, repl, gen)
            fixes.append(f)
        fixes.append(fixups.name_has_slash)
        return fixes, patch

       
class NXP(Vendor):
    abbrev = 'nxp'
    sections = ['diodes', 'bipolar']
    unpack_by_section = True
    download_urls = ['http://www.nxp.com/models/spicespar/zip/' + file
            for file in ['fet.zip', 'power.zip', 'wideband.zip', 'SBD.zip', 
            'SST.zip', 'diodes.zip', 'mmics.zip', 'varicap.zip',
            'basestations.zip', 'complex_discretes.zip']]
    def unpack_diodes(self):
        return env.Command(None, os.path.join('downloads', 'nxp', 'diodes.zip'),
                """
                - unzip -d %(tempdir)s $SOURCE
                md5sum %(tempdir)s/* >> %(csfile)s
                """ % {'tempdir': os.path.join(TEMPDIR, 'nxp', 'diodes'),
                    'csfile': os.path.join(MODEL_SIGDIR, 'nxp_diodes.md5sum')})
    def unpack_bipolar(self):
        return env.Command(None, os.path.join('downloads', 'nxp', 'SST.zip'),
                """
                - unzip -d %(tempdir)s $SOURCE
                md5sum %(tempdir)s/* >> %(csfile)s
                """ % {'tempdir': os.path.join(TEMPDIR, 'nxp', 'bipolar'),
                    'csfile': os.path.join(MODEL_SIGDIR, 'nxp_bipolar.md5sum')})
    
           
    def diodes_fixups(self, modelname, dir):
        ignore_patterns = [
                'BZX384-B.*prm',
                'BZB84-B.*prm',
                'BZV49-C12\.prm',
                'PDZ4V7B\.prm',
                'PZU2\.4.*\.prm',
                'PZU2\.7.*\.prm',
                'PZU3\.0.*\.prm',
                'PZU3\.3.*\.prm',
                'PZU3\.6.*\.prm',
                'PZU3\.9.*\.prm',
                'PZU4\.3.*\.prm',
                'PZU4\.7.*\.prm',
                'PZU5\.1B.*A\.prm',
                'PZU5\.1DB2\.prm',
                'PZU5\.6B.*A\.prm',
                'PZU5\.6DB2\.prm',
                'PZU6\.2B.*A\.prm',
                'PZU6\.2DB2\.prm',
                'PZU6\.8B.*A\.prm',
                'PZU6\.8DB2\.prm',
                'PZU7\.5B.*A\.prm',
                'PZU7\.5DB2\.prm',
                'PZU8\.2B.*A\.prm',
                'PZU8\.2DB2\.prm',
                'PZU9\.1B.*A\.prm',
                'PZU9\.1DB2\.prm']
        string_replacements = {
                'PESD3V3L1BA.prm': ("*.MODEL", ".MODEL" ),
	            '1N4148.prm': (".END", ".ENDS"),
	            'BZX100A.prm': (".MODEL BZX100A", ".MODEL BZX100A D")}
        bzx_3pin = ['BZX84C3V3.prm',
                'BZX84C4V3.prm',
                'BZX84C75.prm']
        for pat in ignore_patterns:
            if re.match(pat, modelname):
                return None, None #these files are duplicate models.  Not needed
        fixes = []
        if modelname in string_replacements:
            query, repl = string_replacements[modelname]
            def f(gen):
                return fixups.replace_string(query, repl, gen)
            fixes.append(f)
        if modelname in bzx_3pin:
            fixes.append(fixups.bzx_pin_renumber)
        fixes += [fixups.trailing_newline, fixups.ends_without_subcircuit]
        patch = None
        return fixes, patch

    def bipolar_fixups(self, modelname, dir):
        string_replacements = {
            "BC327-25.prm": ("BC327-25", "BC327_25"),
            "BC327-40.prm": ("BC327-40", "BC327_40"),
            "BC337-16.prm": ("QBC337-16", "QBC337_16"),
            "BC337-25.prm": ("QBC337-25", "QBC337_25"),
            "BC337-40.prm": ("QBC337-40", "QBC337_40"),
            "BC807-25.prm": ("QBC807-25", "QBC807_25"),
            "BC807-25W.prm": ("QBC807-25W", "QBC807_25W"),
            "BC807-40.prm": ("QBC807-40", "QBC807_40"),
            "BC807-40W.prm": ("QBC807-40W", "QBC807_40W"),
            "BC817-16.prm": ("QBC817-16", "QBC817_16"),
            "BC817-16W.prm": ("QBC817-16W", "QBC817_16W"),
            "BC817-25.prm": ("QBC817-25", "QBC817_25"),
            "BC817-25W.prm": ("QBC817-25W", "QBC817_25W"),
            "BC817-40.prm": ("QBC817-40", "QBC817_40"),
            "BC817-40W.prm": ("QBC817-40W", "QBC817_40W"),
            "BCP52-16.prm": ("QBCP52-16", "QBCP52_16"),
            "BCP53-16.prm": ("QBCP53-16", "QBCP53_16"),
            "BCP54-16.prm": ("QBCP54-16", "QBCP54_16"),
            "BCP55-16.prm": ("QBCP55-16", "QBCP55_16"),
            "BCP56-16.prm": ("QBCP56-16", "QBCP56_16"),
            "2PB709ART.prm": ("QTR1", "TR1"),
            "BCX56.prm": ("1 BCX56 NPN", "1 BCX56" ),
            "PBSS8110AS.prm": ("*.SUBCKT", ".SUBCKT" ),
            "BCV47.prm": ("LE 3 333", "LE 3 33" ),
            "PBSS4540X.prm": ("1 PBSS4540X", "1 PB4540X" ),
            "PBSS5160K.prm": ("*.MODEL", ".MODEL" ),
            "PBSS5160U.prm": ("*.MODEL", ".MODEL" ),
            "PDTC123YT.prm": ("TC2233Y", "TC223Y" ),
            "PXTA14.prm": ("LE 3 333", "LE 3 33" )}
        patches = {'BCP68.prm': 'BCP68.patch'}
        fixes = []
        if modelname in string_replacements:
            query, repl = string_replacements[modelname]
            def f(gen):
                return fixups.replace_string(query, repl, gen)
            fixes.append(f)
        fixes += [fixups.trailing_newline, fixups.ends_without_subcircuit]
        patch = patches.get(modelname, None)
        return fixes, patch

ltc = LinearTechnology()
ti = TexasInstruments()
national = NationalSemiconductor()
nxp = NXP()

mk_aliases(ltc, ti, national, nxp)
