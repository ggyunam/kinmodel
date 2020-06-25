import textwrap
from ..KineticModel import KineticModel


def equations(concs, t, *ks):
    DA1, E, U, DA2, DA3, C = concs
    k1, K, EM, k2L, k2C, kXLC, kXC, kXL, kEH = ks

    I1d = K+EM+DA1+DA2
    I2d = K+DA1

    # Return the equations for concs
    return [(- k1*DA1*E - kXC*DA1*C - 2*kXL*DA1*DA3 + kXLC*DA2 + 2*k2L*DA2
             + 2*k2L*DA3 + k2C*C + k1*K*DA1*E/I1d - k1*DA1**2*E/I1d
             - k1*DA1*DA2*E/I2d),
            - k1*DA1*E - k1*DA2*E - kEH*E,
            + k1*DA1*E + k1*DA2*E + kEH*E,
            (+ kXC*DA1*C + 4*kXL*DA1*DA3 - k1*DA2*E - kXLC*DA2 - k2L*DA2
             - kXC*DA2*C + 2*k2L*DA3 + kXLC*DA3 + k1*DA1**2*E/I1d
             - k1*DA1*DA2*E/I1d + k1*K*DA2*E/I2d),
            (- 2*kXL*DA1*DA3 + kXC*DA2*C - 2*k2L*DA3 - kXLC*DA3
             + k1*DA1*DA2*E/I1d + k1*DA1*DA2*E/I2d),
            (- kXC*DA1*C + kXLC*DA2 - kXC*DA2*C + kXLC*DA3 - k2C*C
             + k1*EM*DA1*E/I1d)]


model = KineticModel(
    name="DA_explicit_DA3_ss",
    description=textwrap.dedent("""\
        Simple model for diacid assembly with explicit consideration of
        linear anhydride intermediates, capped at the trimer (DA3).
        Direct EDC hydrolysis is included.

             DA1 + E ---> I1 + U    (k1)
                  I1 ---> DA1       (kiH)
            I1 + DA1 ---> DA2       (kiL)
            I1 + DA2 ---> DA3       (kiL)
                  I1 ---> C         (kiC)
            DA1 + Cy ---> DA2       (kXC)
           DA1 + DA3 ---> 2*DA2     (2*kXL)
             DA2 + E ---> I2 + U    (k1)
                  I2 ---> DA2       (kiH)
            I2 + DA1 ---> DA3       (kiL)
                 DA2 ---> C + DA1   (kXLC)
                 DA2 ---> 2*DA1     (k2L)
            DA2 + Cy ---> DA3       (kXC)
                 DA3 ---> DA1 + DA2 (2*k2L)
                 DA3 ---> C + DA2   (kXLC)
                   C ---> DA1       (k2C)
                   E ---> U         (kEH)

        Steady-state approximation with K = kiH/kiL and EM=kiC/kiL.
        Orders: k1, K, EM, k2L, k2C, kXLC, kXC, kXL, kEH; DA1, E, U, DA2, DA3, C.\
        """),
    kin_sys=equations,
    ks_guesses=[0.02, 100, 50, 1, 1, 0, 0, 0, 0],
    ks_constant=[],
    conc0_guesses=[100, 400],
    conc0_constant=[0, 0, 0, 0],
    k_var_names=["k1", "K", "EM", "k2L", "k2C", "kXLC", "kXC", "kXL", "kEH"],
    k_const_names=[],
    conc0_var_names=["[DA1]0", "[EDC]0"],
    conc0_const_names=["[U]0", "[DA2]0", "[DA3]0", "[C]0"],
    legend_names=["DA1", "EDC", "Urea", "DA2", "DA3", "Cy"],
    top_plot=[1, 2],
    bottom_plot=[0, 3, 4, 5],
    sort_order=[],
    int_eqn=[
        ],
    int_eqn_desc=[
        ],
    lifetime_conc=[3, 4, 5],
    rectime_conc=[0],
    )