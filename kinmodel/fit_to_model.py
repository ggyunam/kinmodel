"""Interfaces with the KineticModel class to fit experimental data to a
given kinetic model and output the results.

"""
import platform
import numpy as np, scipy
from matplotlib import pyplot as plt, rcParams
from . import _version
from .Dataset import Dataset

# Parameters and settings for plots.
COLORS = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
MARKER_SIZE = 6
FIGURE_SIZE_1 = (2.2, 1.9)
FIGURE_SIZE_2 = (2.2, 3.5)
YLABEL = "C"
XLABEL = "t"
rcParams['font.size'] = 6
rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = ['Arial']
rcParams['lines.linewidth'] = 0.5
rcParams['axes.linewidth'] = 0.5
rcParams['legend.frameon'] = False
rcParams['legend.fontsize'] = 6

# Prevent line breaking and format numbers from np
np.set_printoptions(linewidth=np.nan)
np.set_printoptions(precision=2,suppress=True)


def prepare_text(model, reg_info, dataset_n, num_points, time_exp_factor, 
        filename="", boot_CI=95, full_simulation=True, more_stats=False):
    """Generates the output text.

    The number of points (num_points) for the output simulation and
    integrals must be specified.

    """
    smooth_ts_out, smooth_curves_out, integrals = model.simulate(
            reg_info['fit_ks'], 
            reg_info['fit_concs'][dataset_n], 
            num_points, 
            time_exp_factor*max(reg_info['dataset_times'][dataset_n]))

    num_ks = len(reg_info['fit_ks'])
    num_concs = len(reg_info['fit_concs'][dataset_n])
    # Starting index for dataset-specific concentration parameters.
    conc_start_index = num_ks + num_concs*dataset_n

    dataset_params = reg_info['fit_ks'] + reg_info['fit_concs'][dataset_n]

    cov_stddevs = (reg_info['cov_errors'][:num_ks].tolist()
            + reg_info['cov_errors'][conc_start_index:conc_start_index+num_concs].tolist())
    if 'boot_num' in reg_info and boot_CI:
        boot_k_CIs, boot_conc_CIs = model.bootstrap_param_CIs(reg_info, 
                dataset_n, boot_CI)
        param_CIs = np.append(boot_k_CIs, boot_conc_CIs, axis=1)

    # List of all parameter names, for labeling matrices with all fit
    # parameters included (not just the ones specific to this dataset).
    all_parameter_names = model.parameter_names[:num_ks]
    all_parameter_names += ['']*num_concs*dataset_n
    all_parameter_names += model.parameter_names[num_ks:]
    all_parameter_names += ['']*num_concs*(reg_info['num_datasets']-dataset_n-1)

    if reg_info['dataset_names'][dataset_n]:
        title = ("Regression results for dataset "
                f"{reg_info['dataset_names'][dataset_n]} "
                f"from file \"{filename}\"")
    else:
        title = f"Regression results for file \"{filename}\"" 

    text = title + "\n"
    text += "="*len(title) + "\n"

    text += f"Python version: {platform.python_version()}\n"
    text += f"Numpy version: {np.version.version}\n"
    text += f"Scipy version: {scipy.version.version}\n"
    text += f"kinmodel version: {_version.__version__}\n"
    text += "\n"
    text += "\n"

    text += "Model\n"
    text += "-----\n"
    text += f"Name: {model.name}\n"
    text += f"Description: {model.description}\n"
    text += "\n"
    text += "\n"

    text += "Regression\n"
    text += "----------\n"

    text += "Optimized parameters:\n"
    text += "\n"
    if 'boot_num' in reg_info and boot_CI:
        for n in range(len(dataset_params)):
            text += (f"{model.parameter_names[n]:>{model.len_params}} "
                    f"= {dataset_params[n]:+5e} "
                    f"± {(param_CIs[1][n]-param_CIs[0][n])/2:.1e} "
                    f"({param_CIs[0][n]:+5e}, {param_CIs[1][n]:+5e})\n")
        text += "\n"
        text += (f"Errors are {boot_CI}% confidence intervals from "
                f"bootstrapping ({reg_info['boot_num']} permutations).\n")
    else:
        for n in range(len(dataset_params)):
            text += (f"{model.parameter_names[n]:>{model.len_params}} "
                    f"= {dataset_params[n]:+5e}\n")
    text += "\n"

    text += "Regression info:\n"
    text += "\n"
    text += f"Success: {reg_info['success']}\n"
    text += f"Message: {reg_info['message']}\n"

    text += f"Total points (dof): {reg_info['total_points']} ({reg_info['dof']})\n"
    text += f"Sum square residuals (weighted): {reg_info['ssr']:.2e}\n"
    text += f"Sum square residuals (unweighted): {reg_info['pure_ssr']:.2e}\n"
    text += f"RMSD (unweighted): {reg_info['pure_rmsd']:.2e}\n"
    text += "\n"

    if more_stats:
        text += "Covariance matrix:\n"
        for n in range(reg_info['total_params']):
            text += (f"{all_parameter_names[n]:>{model.len_params}} " 
                    + " ".join(f"{m:+.2e}" for m in reg_info['pcov'][n]) + "\n")
        text += "\n"
        
        text += "Parameter σ from covariance matrix (√diagonal):\n"
        text += " ".join(f"{m:+.1e}" for m in cov_stddevs) + "\n"
        text += "\n"

        text += "Correlation matrix:\n"
        for n in range(reg_info['total_params']):
            text += (f"{all_parameter_names[n]:>{model.len_params}} " 
                    + " ".join(f"{m:+.2f}" for m in reg_info['corr'][n]) + "\n")
        text += "\n"
    text += "\n"

    text += "Simulation\n"
    text += "----------\n"
    text += (f"Points used to generate integrals and concentration vs time "
            f"data: {num_points}\n")
    text += "\n"

    if integrals:
        text += "Integrals:\n"
        text += "\n"
        for n in integrals:
            integral_label = "∫ " + n + " dt"
            text += (f"{integral_label:>{model.len_int_eqn_desc+5}} "
                    f"= {integrals[n]:+5e}\n")
        text += "\n"

    if full_simulation:
        text += "Results:\n"
        text += "\n"
        if 'boot_num' in reg_info and boot_CI:
            boot_CI_data = model.bootstrap_plot_CIs(reg_info, dataset_n, 
                    boot_CI, num_points, time_exp_factor)
            text += ("t " + " ".join(model.legend_names) + " "
                    + " ".join(f"{n}CI− {n}CI+" for n in model.legend_names)
                    + "\n")
            for n in range(len(smooth_ts_out)):
                best_fit_points = " ".join(str(m) for m in smooth_curves_out[n])
                CI_points = " ".join([f"{str(pCI)} {str(mCI)}" 
                        for pCI,mCI in zip(boot_CI_data[0][n], boot_CI_data[1][n])])
                text += (str(smooth_ts_out[n]) + " " + best_fit_points + " " + CI_points + "\n")
        else:
            text += "t " + " ".join(model.legend_names) + "\n"
            
            for n in range(len(smooth_ts_out)):
                text += str(smooth_ts_out[n]) + " " + " ".join(
                    str(m) for m in smooth_curves_out[n]) + "\n"

    return text


def generate_plot(model, reg_info, dataset_n, num_points, time_exp_factor, 
            output_filename, boot_CI=95):
    """Generates the output plot.

    Number of points must be specified. Saved as pdf to output_filename.

    """
    dataset_params = reg_info['fit_ks'] + reg_info['fit_concs'][dataset_n]
    max_time = max(reg_info['dataset_times'][dataset_n])*time_exp_factor

    smooth_ts_plot, smooth_curves_plot, _ = model.simulate(reg_info['fit_ks'], 
            reg_info['fit_concs'][dataset_n], 
            num_points, max_time, integrate=False)

    if 'boot_num' in reg_info and boot_CI:
        boot_CI_plots = model.bootstrap_plot_CIs(reg_info, dataset_n, 
                boot_CI, num_points, time_exp_factor)

    if model.top_plot:
        plt.figure(figsize=FIGURE_SIZE_2)
    else:
        plt.figure(figsize=FIGURE_SIZE_1)

    if model.top_plot:
        plt.subplot(211)
        col = 0
        for n in ([np.array(reg_info['dataset_concs'][dataset_n]).T[m] 
                for m in model.top_plot]):
            plt.scatter(reg_info['dataset_times'][dataset_n], n, c=COLORS[col], 
                    s=MARKER_SIZE, linewidths=0)
            col += 1

        col = 0
        for n in [smooth_curves_plot.T[m] for m in model.top_plot]:
            plt.plot(smooth_ts_plot, n, COLORS[col] + '-')
            col += 1

        if 'boot_num' in reg_info and boot_CI:
            col = 0
            for n in [boot_CI_plots[0].T[m] for m in model.top_plot]:
                plt.plot(smooth_ts_plot, n, COLORS[col] + ':')
                col += 1
            col = 0
            for n in [boot_CI_plots[1].T[m] for m in model.top_plot]:
                plt.plot(smooth_ts_plot, n, COLORS[col] + ':')
                col += 1

        plt.legend([model.legend_names[n] for n in model.top_plot], loc=4)

        plt.ylim(ymin=0)
        plt.xlim(xmin=0, xmax=smooth_ts_plot[-1])

        plt.ylabel(YLABEL)

    if model.bottom_plot:
        if model.top_plot:
            plt.subplot(212)
        else:
            plt.subplot(111)

        col = 0
        for n in ([np.array(reg_info['dataset_concs'][dataset_n]).T[m] 
                for m in model.bottom_plot]):
            plt.scatter(reg_info['dataset_times'][dataset_n], n, c=COLORS[col], 
                    s=MARKER_SIZE, linewidths=0, zorder=2)
            col += 1

        col = 0
        for n in [smooth_curves_plot.T[n] for n in model.bottom_plot]:
            plt.plot(smooth_ts_plot, n, COLORS[col] + '-', zorder=3)
            col += 1

        if 'boot_num' in reg_info and boot_CI:
            col = 0
            for n in [boot_CI_plots[0].T[m] for m in model.bottom_plot]:
                plt.plot(smooth_ts_plot, n, COLORS[col] + ':')
                col += 1
            col = 0
            for n in [boot_CI_plots[1].T[m] for m in model.bottom_plot]:
                plt.plot(smooth_ts_plot, n, COLORS[col] + ':')
                col += 1

        plt.legend([model.legend_names[n] for n in model.bottom_plot], loc=2)

        plt.ylim(ymin=0)
        plt.xlim(xmin=0, xmax=smooth_ts_plot[-1])

        plt.xlabel(XLABEL)
        plt.ylabel(YLABEL)

        # Print parameters on plot.
        pars_to_print = ""
        for n in range(len(dataset_params)):
            pars_to_print += "{} = {:.2e}\n".format(model.parameter_names[n], 
                    dataset_params[n])
        plt.text(0.5, 0.2, pars_to_print, transform=plt.gca().transAxes, fontsize=6)
    
    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()


def fit_and_output(model, data_filename,
            text_output_points=3000, text_time_extension_factor=3.0, 
            text_output=True, plot_output_points=1000, 
            plot_time_extension_factor=1.1, 
            text_full_output=True, monitor=False, 
            bootstrap_iterations=100, bootstrap_CI=95, more_stats=False):
    """Carry out the fit of the model and output the data.

    """
    datasets = Dataset.read_raw_data(model, data_filename)

    reg_info = model.fit_to_model(datasets, monitor=monitor, 
        N_boot=bootstrap_iterations)        

    for n in range(reg_info['num_datasets']):
        output_text = prepare_text(model, reg_info, n, text_output_points, 
                text_time_extension_factor, data_filename, bootstrap_CI, 
                text_full_output, more_stats)
        if text_output:
            text_output_filename = f"{data_filename}_{model.name}_{reg_info['dataset_names'][n]}.txt"
            with open(text_output_filename, 'w', encoding='utf-8') as write_file:
                print(output_text, file=write_file)
        else:
            print(output_text)

    if plot_output_points:
        for n in range(reg_info['num_datasets']):
            plot_output_filename = f"{data_filename}_{model.name}_{reg_info['dataset_names'][n]}.pdf"
            generate_plot(model, reg_info, n, plot_output_points, 
                    plot_time_extension_factor, plot_output_filename, 
                    bootstrap_CI)
