<?xml version="1.0" encoding="UTF-8"?>
<drawing version="7">
    <attr value="xbr" name="DeviceFamilyName">
        <trait delete="all:0" />
        <trait editname="all:0" />
        <trait edittrait="all:0" />
    </attr>
    <netlist>
        <signal name="XLXN_1" />
        <signal name="XLXN_6" />
        <signal name="CLK" />
        <signal name="XLXN_4" />
        <signal name="CLK_D" />
        <signal name="XLXN_29" />
        <signal name="XLXN_30" />
        <signal name="XLXN_34" />
        <signal name="XLXN_35" />
        <port polarity="Input" name="CLK" />
        <port polarity="Output" name="CLK_D" />
        <blockdef name="ld">
            <timestamp>2000-1-1T10:10:10</timestamp>
            <rect width="256" x="64" y="-320" height="256" />
            <line x2="320" y1="-256" y2="-256" x1="384" />
            <line x2="64" y1="-256" y2="-256" x1="0" />
            <line x2="64" y1="-128" y2="-128" x1="0" />
        </blockdef>
        <blockdef name="xor2">
            <timestamp>2000-1-1T10:10:10</timestamp>
            <line x2="64" y1="-64" y2="-64" x1="0" />
            <line x2="60" y1="-128" y2="-128" x1="0" />
            <line x2="208" y1="-96" y2="-96" x1="256" />
            <arc ex="44" ey="-144" sx="48" sy="-48" r="56" cx="16" cy="-96" />
            <arc ex="64" ey="-144" sx="64" sy="-48" r="56" cx="32" cy="-96" />
            <line x2="64" y1="-144" y2="-144" x1="128" />
            <line x2="64" y1="-48" y2="-48" x1="128" />
            <arc ex="128" ey="-144" sx="208" sy="-96" r="88" cx="132" cy="-56" />
            <arc ex="208" ey="-96" sx="128" sy="-48" r="88" cx="132" cy="-136" />
        </blockdef>
        <blockdef name="pullup">
            <timestamp>2000-1-1T10:10:10</timestamp>
            <line x2="64" y1="-108" y2="-128" x1="64" />
            <line x2="64" y1="-104" y2="-108" x1="80" />
            <line x2="80" y1="-88" y2="-104" x1="48" />
            <line x2="48" y1="-72" y2="-88" x1="80" />
            <line x2="80" y1="-56" y2="-72" x1="48" />
            <line x2="48" y1="-48" y2="-56" x1="64" />
            <line x2="64" y1="-32" y2="-48" x1="64" />
            <line x2="64" y1="-56" y2="-48" x1="48" />
            <line x2="48" y1="-72" y2="-56" x1="80" />
            <line x2="80" y1="-88" y2="-72" x1="48" />
            <line x2="48" y1="-104" y2="-88" x1="80" />
            <line x2="80" y1="-108" y2="-104" x1="64" />
            <line x2="64" y1="0" y2="-32" x1="64" />
            <line x2="32" y1="-128" y2="-128" x1="96" />
        </blockdef>
        <block symbolname="ld" name="XLXI_2">
            <blockpin signalname="CLK" name="D" />
            <blockpin signalname="XLXN_4" name="G" />
            <blockpin signalname="XLXN_1" name="Q" />
        </block>
        <block symbolname="ld" name="XLXI_5">
            <blockpin signalname="XLXN_1" name="D" />
            <blockpin signalname="XLXN_4" name="G" />
            <blockpin signalname="XLXN_6" name="Q" />
        </block>
        <block symbolname="pullup" name="XLXI_4">
            <blockpin signalname="XLXN_4" name="O" />
        </block>
        <block symbolname="xor2" name="XLXI_3">
            <blockpin signalname="XLXN_6" name="I0" />
            <blockpin signalname="CLK" name="I1" />
            <blockpin signalname="CLK_D" name="O" />
        </block>
    </netlist>
    <sheet sheetnum="1" width="3520" height="2720">
        <instance x="1568" y="1472" name="XLXI_5" orien="R0" />
        <branch name="XLXN_1">
            <wire x2="1568" y1="1216" y2="1216" x1="1536" />
        </branch>
        <instance x="1152" y="1472" name="XLXI_2" orien="R0" />
        <branch name="CLK">
            <wire x2="1136" y1="1056" y2="1056" x1="1120" />
            <wire x2="1984" y1="1056" y2="1056" x1="1136" />
            <wire x2="1136" y1="1056" y2="1216" x1="1136" />
            <wire x2="1152" y1="1216" y2="1216" x1="1136" />
        </branch>
        <instance x="1984" y="1184" name="XLXI_3" orien="R0" />
        <branch name="CLK_D">
            <wire x2="2256" y1="1088" y2="1088" x1="2240" />
        </branch>
        <iomarker fontsize="28" x="2256" y="1088" name="CLK_D" orien="R0" />
        <branch name="XLXN_6">
            <wire x2="1968" y1="1216" y2="1216" x1="1952" />
            <wire x2="1984" y1="1120" y2="1120" x1="1968" />
            <wire x2="1968" y1="1120" y2="1216" x1="1968" />
        </branch>
        <iomarker fontsize="28" x="1120" y="1056" name="CLK" orien="R180" />
        <branch name="XLXN_4">
            <wire x2="1040" y1="1424" y2="1440" x1="1040" />
            <wire x2="1136" y1="1440" y2="1440" x1="1040" />
            <wire x2="1552" y1="1440" y2="1440" x1="1136" />
            <wire x2="1152" y1="1344" y2="1344" x1="1136" />
            <wire x2="1136" y1="1344" y2="1440" x1="1136" />
            <wire x2="1568" y1="1344" y2="1344" x1="1552" />
            <wire x2="1552" y1="1344" y2="1440" x1="1552" />
        </branch>
        <instance x="976" y="1424" name="XLXI_4" orien="R0" />
    </sheet>
</drawing>
