"""Defines the Dataset class.

"""
import string
import numpy as np


class Dataset:
    def __init__(self, name="", times=None, concs=None):
        self.name = name
        self.times = times
        self.concs = concs

    @property
    def total_data_points(self):
        return self.concs.size - np.isnan(self.concs).sum()

    @property
    def num_times(self):
        return len(self.times)

    @property
    def max_time(self):
        return max(self.times)

    @classmethod
    def read_raw_data(cls, model, data_filename) -> ['Dataset']:
        """Load data from file, formated as a csv file.

        File is assumed to have the following structure:
            - Rows with only the first cell filled with a string (not
              interpretable as a number) and the remaining cells empty
              are titles for new datasets, which follow. Each experiment
              must have a title after the first.
            - All rows with the first column interpretable as a number
              are assumed to contain data.
            - All other rows ignored.

        """

        def _is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        with open(data_filename) as datafile:
            datasets = [cls()]
            all_times = []
            all_concs = []
            curr_ds_times = []
            curr_ds_concs = []
            for line in datafile:
                curline = line.replace("\n", "").split(",")
                if _is_number(curline[0]):
                    # Line contains data
                    curr_ds_times.append(float(curline[0]))
                    line_concs = []
                    for n in range(model.num_data_concs):
                        if n+1 < len(curline):
                            if curline[n+1] != "":
                                line_concs.append(float(curline[n+1]))
                            else:
                                line_concs.append(np.nan)
                        else:
                            line_concs.append(np.nan)
                    curr_ds_concs.append(line_concs)
                elif curline[0] != '' and curline[1:] == ['']*(len(curline)-1):
                    # Line contains dataset name
                    if curr_ds_times:
                        # A dataset already exists, move on to next one
                        all_times.append(curr_ds_times)
                        all_concs.append(curr_ds_concs)
                        curr_ds_times = []
                        curr_ds_concs = []
                        datasets.append(cls())
                        datasets[-1].name = "".join(
                                c for c in curline[0] if c in string.printable)
                    else:
                        # This is the first dataset
                        datasets[-1].name = "".join(
                                c for c in curline[0] if c in string.printable)
            # Record times for last dataset
            all_times.append(curr_ds_times)
            all_concs.append(curr_ds_concs)

            # Sort and store data for all datasets
            for s in range(len(datasets)):
                datasets[s].times = np.array(all_times[s])
                unsorted_data = np.array(all_concs[s])
                sorted_data = np.empty_like(unsorted_data)
                for n in range(model.num_data_concs):
                    sorted_data[:, n] = unsorted_data[:, model.sort_order[n]]
                datasets[s].concs = sorted_data

        return datasets

    @classmethod
    def boot_randomX(self, N, datasets, force1st=True) -> [['Dataset']]:
        """Generates datasets using a non-parametric random X bootstrap
        method. Subsets of the data are generated by filling with
        randomly chosen time points from the original data. Returns a
        list of lists of Datasets.
        """
        def sort_data(times, concs):
            sorted_times = np.array(sorted(times))
            sorted_concs = np.array([c for _, c in sorted(
                    list(zip(times, concs)), key=lambda x: x[0])])
            return sorted_times, sorted_concs

        boot_datasets = []
        for i in range(N):
            current_datasets = []
            for d in datasets:
                if force1st:
                    new_concs = np.array([d.concs[0]])
                    new_times = np.array([d.times[0]])
                    while len(new_times) < len(d.times):
                        x = np.random.randint(1, d.num_times)
                        new_concs = np.append(new_concs, [d.concs[x]], axis=0)
                        new_times = np.append(new_times, [d.times[x]], axis=0)
                else:
                    new_concs = np.empty((0, self.num_data_concs))
                    new_times = np.array([])
                    for n in range(0, d.num_times):
                        x = np.random.randint(0, d.num_times)
                        new_concs = np.append(new_concs, [d.concs[x]], axis=0)
                        new_times = np.append(new_times, [d.times[x]], axis=0)
                sorted_times, sorted_concs = sort_data(new_times, new_concs)
                current_datasets.append(Dataset(
                        times=sorted_times, concs=sorted_concs))

            boot_datasets.append(current_datasets)

        return boot_datasets

    @classmethod
    def boot_fixedX(self, N, times, model_ys, residuals) -> [['Dataset']]:
        """Generates datasets using a non-parametric fixed X bootstrap
        method. A random residual is added to each predicted data point.
        """
        def rand_residual(residuals, d, c):
            r = np.nan
            while np.isnan(r):
                r = np.random.choice(residuals[d][c])
            return r

        num_datasets = len(model_ys)
        num_concs0 = model_ys[0].shape[1]
        boot_datasets = []
        for i in range(N):
            # Perturbed datasets that can be fit.
            current_datasets = []
            for d in range(num_datasets):
                new_concs = np.empty((0, num_concs0))
                new_concs_t0 = []
                # Leave starting conc 0's as 0's. These are not
                # unknowns.
                for c in range(num_concs0):
                    conc = model_ys[d][0][c]
                    if not np.isnan(conc) and conc != 0:
                        new_concs_t0.append(
                                conc + rand_residual(residuals, d, c))
                    else:
                        new_concs_t0.append(conc)
                new_concs = np.append(new_concs, [new_concs_t0], axis=0)

                for n in range(1, len(model_ys[d])):
                    new_concs_t = []
                    for c in range(len(model_ys[d][n])):
                        conc = model_ys[d][n][c]
                        if not np.isnan(conc):
                            new_concs_t.append(
                                    conc + rand_residual(residuals, d, c))
                        else:
                            new_concs_t.append(np.nan)
                    new_concs = np.append(new_concs, [np.array(new_concs_t)],
                                          axis=0)
                current_datasets.append(Dataset(times=times[d], concs=new_concs))

            boot_datasets.append(current_datasets)

        return boot_datasets
