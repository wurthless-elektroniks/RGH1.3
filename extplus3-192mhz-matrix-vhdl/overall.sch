<?xml version="1.0" encoding="UTF-8"?>
<drawing version="7">
    <attr value="xbr" name="DeviceFamilyName">
        <trait delete="all:0" />
        <trait editname="all:0" />
        <trait edittrait="all:0" />
    </attr>
    <netlist>
        <signal name="RST" />
        <signal name="DBG" />
        <signal name="XLXN_6" />
        <signal name="XLXN_7" />
        <signal name="EXTC" />
        <signal name="POST" />
        <signal name="XLXN_11" />
        <signal name="CLK" />
        <signal name="XLXN_16" />
        <port polarity="BiDirectional" name="RST" />
        <port polarity="Output" name="DBG" />
        <port polarity="Output" name="EXTC" />
        <port polarity="Input" name="POST" />
        <port polarity="Input" name="CLK" />
        <blockdef name="post_proc">
            <timestamp>2021-5-26T4:9:50</timestamp>
            <rect width="256" x="64" y="-192" height="192" />
            <line x2="0" y1="-160" y2="-160" x1="64" />
            <line x2="0" y1="-32" y2="-32" x1="64" />
            <line x2="384" y1="-160" y2="-160" x1="320" />
            <line x2="384" y1="-96" y2="-96" x1="320" />
            <line x2="384" y1="-32" y2="-32" x1="320" />
            <line x2="64" y1="-96" y2="-96" x1="0" />
        </blockdef>
        <blockdef name="divider_slow">
            <timestamp>2021-4-28T14:41:42</timestamp>
            <rect width="256" x="64" y="-64" height="64" />
            <line x2="0" y1="-32" y2="-32" x1="64" />
            <line x2="384" y1="-32" y2="-32" x1="320" />
        </blockdef>
        <blockdef name="slower">
            <timestamp>2022-5-18T21:25:26</timestamp>
            <line x2="0" y1="-96" y2="-96" x1="64" />
            <line x2="0" y1="-32" y2="-32" x1="64" />
            <rect width="256" x="64" y="-128" height="128" />
            <line x2="384" y1="-32" y2="-32" x1="320" />
            <line x2="320" y1="-96" y2="-96" x1="384" />
        </blockdef>
        <blockdef name="clk_doubler">
            <timestamp>2021-5-28T3:53:37</timestamp>
            <rect width="256" x="64" y="-64" height="64" />
            <line x2="0" y1="-32" y2="-32" x1="64" />
            <line x2="384" y1="-32" y2="-32" x1="320" />
        </blockdef>
        <block symbolname="post_proc" name="XLXI_3">
            <blockpin signalname="XLXN_16" name="CLK" />
            <blockpin signalname="XLXN_6" name="to_slow" />
            <blockpin signalname="DBG" name="DBG" />
            <blockpin signalname="RST" name="RST" />
            <blockpin signalname="POST" name="POST" />
            <blockpin signalname="XLXN_11" name="callback" />
        </block>
        <block symbolname="divider_slow" name="XLXI_4">
            <blockpin signalname="CLK" name="CLK" />
            <blockpin signalname="XLXN_7" name="CLK_S" />
        </block>
        <block symbolname="slower" name="XLXI_5">
            <blockpin signalname="XLXN_7" name="CLK" />
            <blockpin signalname="XLXN_6" name="in_slow" />
            <blockpin signalname="EXTC" name="EXTC" />
            <blockpin signalname="XLXN_11" name="callback" />
        </block>
        <block symbolname="clk_doubler" name="XLXI_7">
            <blockpin signalname="CLK" name="CLK" />
            <blockpin signalname="XLXN_16" name="CLK_D" />
        </block>
    </netlist>
    <sheet sheetnum="1" width="3520" height="2720">
        <instance x="1648" y="1472" name="XLXI_3" orien="R0">
        </instance>
        <branch name="RST">
            <wire x2="2048" y1="1440" y2="1440" x1="2032" />
        </branch>
        <iomarker fontsize="28" x="2048" y="1440" name="RST" orien="R0" />
        <branch name="DBG">
            <wire x2="2048" y1="1376" y2="1376" x1="2032" />
        </branch>
        <iomarker fontsize="28" x="2048" y="1376" name="DBG" orien="R0" />
        <branch name="XLXN_6">
            <wire x2="2208" y1="1312" y2="1312" x1="2032" />
        </branch>
        <branch name="XLXN_7">
            <wire x2="2192" y1="1600" y2="1600" x1="2032" />
            <wire x2="2208" y1="1376" y2="1376" x1="2192" />
            <wire x2="2192" y1="1376" y2="1600" x1="2192" />
        </branch>
        <instance x="2208" y="1408" name="XLXI_5" orien="R0">
        </instance>
        <branch name="EXTC">
            <wire x2="2608" y1="1376" y2="1376" x1="2592" />
        </branch>
        <iomarker fontsize="28" x="2608" y="1376" name="EXTC" orien="R0" />
        <branch name="POST">
            <wire x2="1648" y1="1376" y2="1376" x1="1632" />
        </branch>
        <branch name="XLXN_11">
            <wire x2="1632" y1="1200" y2="1312" x1="1632" />
            <wire x2="1648" y1="1312" y2="1312" x1="1632" />
            <wire x2="2608" y1="1200" y2="1200" x1="1632" />
            <wire x2="2608" y1="1200" y2="1312" x1="2608" />
            <wire x2="2608" y1="1312" y2="1312" x1="2592" />
        </branch>
        <iomarker fontsize="28" x="1632" y="1376" name="POST" orien="R180" />
        <instance x="1152" y="1472" name="XLXI_7" orien="R0">
        </instance>
        <iomarker fontsize="28" x="1120" y="1440" name="CLK" orien="R180" />
        <branch name="XLXN_16">
            <wire x2="1552" y1="1440" y2="1440" x1="1536" />
            <wire x2="1648" y1="1440" y2="1440" x1="1552" />
        </branch>
        <branch name="CLK">
            <wire x2="1136" y1="1440" y2="1440" x1="1120" />
            <wire x2="1152" y1="1440" y2="1440" x1="1136" />
            <wire x2="1136" y1="1440" y2="1600" x1="1136" />
            <wire x2="1632" y1="1600" y2="1600" x1="1136" />
            <wire x2="1648" y1="1600" y2="1600" x1="1632" />
        </branch>
        <instance x="1648" y="1632" name="XLXI_4" orien="R0">
        </instance>
    </sheet>
</drawing>