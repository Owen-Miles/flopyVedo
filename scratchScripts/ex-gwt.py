import os
import sys
import matplotlib.pyplot as plt
import flopy
import numpy as np

mf6exe = "./models/mf6.exe"
exe_name_mf = "./models/mf2005.exe"
exe_name_mt = "./models/mt3dms.exe"
ws = "./working/"

parameters = {
    "ex-gwt-mt3dms-p01a": {
        "dispersivity": 0.0,
        "retardation": 1.0,
        "decay": 0.0,
    },
    "ex-gwt-mt3dms-p01b": {
        "dispersivity": 10.0,
        "retardation": 1.0,
        "decay": 0.0,
    },
    "ex-gwt-mt3dms-p01c": {
        "dispersivity": 10.0,
        "retardation": 5.0,
        "decay": 0.0,
    },
    "ex-gwt-mt3dms-p01d": {
        "dispersivity": 10.0,
        "retardation": 5.0,
        "decay": 0.002,
    },
}

parameter_units = {
    "dispersivity": "$m$",
    "retardation": "unitless",
    "decay": "$d^{-1}$",
}

length_units = "meters"
time_units = "days"


nper = 1  # Number of periods
nlay = 1  # Number of layers
ncol = 101  # Number of columns
nrow = 1  # Number of rows
delr = 10.0  # Column width ($m$)
delc = 1.0  # Row width ($m$)
top = 0.0  # Top of the model ($m$)
botm = -1.0  # Layer bottom elevations ($m$)
prsity = 0.25  # Porosity
perlen = 2000  # Simulation time ($days$)
k11 = 1.0  # Horizontal hydraulic conductivity ($m/d$)

k33 = k11  # Vertical hydraulic conductivity ($m/d$)
laytyp = 1
nstp = 100.0
dt0 = perlen / nstp
Lx = (ncol - 1) * delr
v = 0.24
q = v * prsity
h1 = q * Lx
strt = np.zeros((nlay, nrow, ncol), dtype=float)
strt[0, 0, 0] = h1  # Starting head ($m$)
l = 1000.0  # Needed for plots
icelltype = 1  # Cell conversion type
ibound = np.ones((nlay, nrow, ncol), dtype=int)
ibound[0, 0, 0] = -1
ibound[0, 0, -1] = -1

mixelm = 0  # TVD
rhob = 0.25
sp2 = 0.0  # red, but not used in this problem
sconc = np.zeros((nlay, nrow, ncol), dtype=float)
dmcoef = 0.0  # Molecular diffusion coefficient
# Set solver parameter values (and related)
nouter, ninner = 100, 300
hclose, rclose, relax = 1e-6, 1e-6, 1.0
ttsmult = 1.0


# time stuff
tdis_rc = []
tdis_rc.append((perlen, nstp, 1.0))

# boundary conditions
chdspd = [[(0, 0, 0), h1], [(0, 0, ncol - 1), 0.0]]
c0 = 1.0
cncspd = [[(0, 0, 0), c0]]

def build_model(
    sim_name,
    dispersivity=0.0,
    retardation=0.0,
    decay=0.0,
    mixelm=0,
    silent=False,
):
    if buildModel:
        # MODFLOW 6
        name = "p01-mf6"
        gwfname = "gwf-" + name
        sim_ws = os.path.join(ws, sim_name)
        sim = flopy.mf6.MFSimulation(
            sim_name=sim_name, sim_ws=sim_ws, exe_name=mf6exe
        )

        # Instantiating MODFLOW 6 time discretization
        flopy.mf6.ModflowTdis(
            sim, nper=nper, perioddata=tdis_rc, time_units=time_units
        )

        # Instantiating MODFLOW 6 groundwater flow model
        gwf = flopy.mf6.ModflowGwf(
            sim,
            modelname=gwfname,
            save_flows=True,
            model_nam_file="{}.nam".format(gwfname),
        )

        # Instantiating MODFLOW 6 solver for flow model
        imsgwf = flopy.mf6.ModflowIms(
            sim,
            print_option="SUMMARY",
            outer_dvclose=hclose,
            outer_maximum=nouter,
            under_relaxation="NONE",
            inner_maximum=ninner,
            inner_dvclose=hclose,
            rcloserecord=rclose,
            linear_acceleration="CG",
            scaling_method="NONE",
            reordering_method="NONE",
            relaxation_factor=relax,
            filename="{}.ims".format(gwfname),
        )
        sim.register_ims_package(imsgwf, [gwf.name])

        # Instantiating MODFLOW 6 discretization package
        flopy.mf6.ModflowGwfdis(
            gwf,
            length_units=length_units,
            nlay=nlay,
            nrow=nrow,
            ncol=ncol,
            delr=delr,
            delc=delc,
            top=top,
            botm=botm,
            idomain=np.ones((nlay, nrow, ncol), dtype=int),
            filename="{}.dis".format(gwfname),
        )

        # Instantiating MODFLOW 6 node-property flow package
        flopy.mf6.ModflowGwfnpf(
            gwf,
            save_flows=False,
            icelltype=icelltype,
            k=k11,
            k33=k33,
            save_specific_discharge=True,
            filename="{}.npf".format(gwfname),
        )

        # Instantiating MODFLOW 6 initial conditions package for flow model
        flopy.mf6.ModflowGwfic(
            gwf, strt=strt, filename="{}.ic".format(gwfname)
        )

        # Instantiating MODFLOW 6 constant head package
        flopy.mf6.ModflowGwfchd(
            gwf,
            maxbound=len(chdspd),
            stress_period_data=chdspd,
            save_flows=False,
            pname="CHD-1",
            filename="{}.chd".format(gwfname),
        )

        # Instantiating MODFLOW 6 output control package for flow model
        flopy.mf6.ModflowGwfoc(
            gwf,
            head_filerecord="{}.hds".format(gwfname),
            budget_filerecord="{}.cbc".format(gwfname),
            headprintrecord=[
                ("COLUMNS", 10, "WIDTH", 15, "DIGITS", 6, "GENERAL")
            ],
            saverecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
            printrecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
        )

        # Instantiating MODFLOW 6 groundwater transport package
        gwtname = "gwt-" + name
        gwt = flopy.mf6.MFModel(
            sim,
            model_type="gwt6",
            modelname=gwtname,
            model_nam_file="{}.nam".format(gwtname),
        )
        gwt.name_file.save_flows = True
        imsgwt = flopy.mf6.ModflowIms(
            sim,
            print_option="SUMMARY",
            outer_dvclose=hclose,
            outer_maximum=nouter,
            under_relaxation="NONE",
            inner_maximum=ninner,
            inner_dvclose=hclose,
            rcloserecord=rclose,
            linear_acceleration="BICGSTAB",
            scaling_method="NONE",
            reordering_method="NONE",
            relaxation_factor=relax,
            filename="{}.ims".format(gwtname),
        )
        sim.register_ims_package(imsgwt, [gwt.name])

        # Instantiating MODFLOW 6 transport discretization package
        flopy.mf6.ModflowGwtdis(
            gwt,
            nlay=nlay,
            nrow=nrow,
            ncol=ncol,
            delr=delr,
            delc=delc,
            top=top,
            botm=botm,
            idomain=1,
            filename="{}.dis".format(gwtname),
        )

        # Instantiating MODFLOW 6 transport initial concentrations
        flopy.mf6.ModflowGwtic(
            gwt, strt=sconc, filename="{}.ic".format(gwtname)
        )

        # Instantiating MODFLOW 6 transport advection package
        if mixelm == 0:
            scheme = "UPSTREAM"
        elif mixelm == -1:
            scheme = "TVD"
        else:
            raise Exception()
        flopy.mf6.ModflowGwtadv(
            gwt, scheme=scheme, filename="{}.adv".format(gwtname)
        )

        # Instantiating MODFLOW 6 transport dispersion package
        if dispersivity != 0:
            flopy.mf6.ModflowGwtdsp(
                gwt,
                xt3d_off=True,
                alh=dispersivity,
                ath1=dispersivity,
                filename="{}.dsp".format(gwtname),
            )

        # Instantiating MODFLOW 6 transport mass storage package (formerly "reaction" package in MT3DMS)
        if retardation != 1.0:
            sorption = "linear"
            kd = (
                (retardation - 1.0) * prsity / rhob
            )  # prsity & rhob defined in
        else:  # global variable section
            sorption = None
            kd = 1.0
        if decay != 0.0:
            first_order_decay = True
        else:
            first_order_decay = False
        flopy.mf6.ModflowGwtmst(
            gwt,
            porosity=prsity,
            sorption=sorption,
            bulk_density=rhob,
            distcoef=kd,
            first_order_decay=first_order_decay,
            decay=decay,
            decay_sorbed=decay,
            filename="{}.mst".format(gwtname),
        )

        # Instantiating MODFLOW 6 transport constant concentration package
        flopy.mf6.ModflowGwtcnc(
            gwt,
            maxbound=len(cncspd),
            stress_period_data=cncspd,
            save_flows=False,
            pname="CNC-1",
            filename="{}.cnc".format(gwtname),
        )

        # Instantiating MODFLOW 6 transport source-sink mixing package
        flopy.mf6.ModflowGwtssm(
            gwt, sources=[[]], filename="{}.ssm".format(gwtname)
        )

        # Instantiating MODFLOW 6 transport output control package
        flopy.mf6.ModflowGwtoc(
            gwt,
            budget_filerecord="{}.cbc".format(gwtname),
            concentration_filerecord="{}.ucn".format(gwtname),
            concentrationprintrecord=[
                ("COLUMNS", 10, "WIDTH", 15, "DIGITS", 6, "GENERAL")
            ],
            saverecord=[("CONCENTRATION", "LAST"), ("BUDGET", "LAST")],
            printrecord=[("CONCENTRATION", "LAST"), ("BUDGET", "LAST")],
        )

        # Instantiating MODFLOW 6 flow-transport exchange mechanism
        flopy.mf6.ModflowGwfgwt(
            sim,
            exgtype="GWF6-GWT6",
            exgmnamea=gwfname,
            exgmnameb=gwtname,
            filename="{}.gwfgwt".format(name),
        )
        # return mf, mt, sim
        return sim

    return None


def write_model(sim, silent=True):
    sim.write_simulation(silent=silent)


def run_model(sim, silent=True):
    success = True
    success, buff = sim.run_simulation(silent=silent)
    if not success:
        print(buff)
    return success


def plot_results(mf6, idx, ax=None):
    if plotModel:
        mf6_out_path = mf6.simulation_data.mfpath.get_sim_path()
        mf6.simulation_data.mfpath.get_sim_path()

        # Get the MF6 concentration output
        fname_mf6 = os.path.join(
            mf6_out_path, list(mf6.model_names)[1] + ".ucn"
        )
        ucnobj_mf6 = flopy.utils.HeadFile(
            fname_mf6, precision="double", text="CONCENTRATION"
        )

        conc_mf6 = ucnobj_mf6.get_alldata()

        # Create figure for scenario
        if ax is None:
            fig, ax = plt.subplots(
                1, 1, tight_layout=True
            )

        ax.plot(
            np.linspace(0, l, ncol),
            conc_mf6[0, 0, 0, :],
            "^",
            markeredgewidth=0.5,
            color="blue",
            fillstyle="none",
            label="MF6",
            markersize=3,
        )
        ax.set_ylim(0, 1.1)
        ax.set_xlim(0, 1000)
        ax.set_xlabel("Distance, in m")
        ax.set_ylabel("Concentration")

        ax.legend()


def scenario(idx, silent=False):
    key = list(parameters.keys())[idx]
    parameter_dict = parameters[key]

    sim = build_model(key, **parameter_dict)
    write_model(sim, silent=silent)
    success = run_model(sim, silent=silent)
    if success:
        plot_results(sim, idx)


plotModel = True
buildModel = True

# advection
scenario(0)
plt.show()

# #advection and dispersion
scenario(1)
plt.show()

# #advection dispersion and retardation
# scenario(2)
# plt.show()

# #advection dispersion retardation and decay
# scenario(3)
# plt.show()
