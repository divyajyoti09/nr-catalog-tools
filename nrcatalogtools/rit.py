# Copyright (C) 2023 Prayush Kumar
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import glob
import os
import pandas as pd
import pathlib
import requests
# import sxs


def url_exists(link):
    requests.packages.urllib3.disable_warnings()
    for n in range(100):
        try:
            response = requests.head(link, verify=False)
            if response.status_code == requests.codes.ok:
                return True
            else:
                return False
        except:
            continue


class RITCatalog():
    def __init__(
            self,
            catalog_name='RIT',
            catalog_url='https://ccrgpages.rit.edu/~RITCatalog/',
            metadata_file_fmts=[
                'RIT:BBH:{:04d}-n{:3d}-id{:d}_Metadata.txt',
                'RIT:eBBH:{:04d}-n{:3d}-ecc_Metadata.txt',
            ],
            waveform_file_fmt='ExtrapStrain_RIT-BBH-{:04d}-n{:3d}.h5',
            waveform_file_fmts=[
                'ExtrapStrain_RIT-BBH-{:04d}-n{:3d}.h5',
                'ExtrapStrain_RIT-eBBH-{:04d}-n{:3d}.h5',
            ],
            possible_resolutions=[100, 120, 88, 118, 130, 140, 144, 160, 200],
            max_id_val=6,
            cache_dir='~/.nr_data/',
            use_cache=True,
            verbosity=0):
        self.verbosity = verbosity
        self.catalog_url = catalog_url
        self.use_cache = use_cache
        self.cache_dir = pathlib.Path(
            os.path.abspath(os.path.expanduser(cache_dir)))

        self.num_of_sims = 0

        self.metadata_url = self.catalog_url + '/Metadata/'
        self.metadata_file_fmts = metadata_file_fmts
        self.metadata = pd.DataFrame.from_dict({})
        self.metadata_dir = self.cache_dir / catalog_name / "metadata"

        self.waveform_data = {}
        self.waveform_data_url = self.catalog_url + '/Data/'
        self.waveform_file_fmt = waveform_file_fmt
        self.waveform_data_dir = self.cache_dir / catalog_name / "waveform_data"

        self.possible_res = possible_resolutions
        self.max_id_val = max_id_val

        internal_dirs = [
            self.cache_dir, self.metadata_dir, self.waveform_data_dir
        ]
        for d in internal_dirs:
            d.mkdir(parents=True, exist_ok=True)

    def simname_from_metadata_filename(self, filename):
        return filename.split('_Meta')[0]

    def metadata_filename_from_simname(self, sim_name):
        '''
        We assume the sim names are either of the format:
        (1) RIT:eBBH:1109-n100-ecc
        (2) RIT:BBH:1109-n100-id1
        '''
        txt = sim_name.split(':')[-1]
        idx = int(txt[:4])
        res = int(txt.split('-')[1][1:])
        if 'eBBH' not in sim_name:
            # If this works, its a quasicircular sim
            id_val = int(txt[-1])
            return self.metadata_file_fmts[0].format(idx, res, id_val)
        else:
            return self.metadata_file_fmts[1].format(idx, res)

    def metadata_filename_from_cache(self, idx):
        possible_sim_tags = self.simtags(idx)
        for sim_tag in possible_sim_tags:
            mf = self.metadata_dir / sim_tag
            poss_files = glob.glob(str(mf) + "*")
            if len(poss_files) == 0:
                if self.verbosity > 4:
                    print(
                        "...found no files matching {}".format(str(mf) + "*"))
                continue
            file_name = poss_files[0]
        return file_name

    def waveform_filename_from_simname(self, sim_name):
        '''
        ExtrapStrain_RIT-BBH-0005-n100.h5 --> 
        ExtrapStrain_RIT-eBBH-1843-n100.h5
        RIT:eBBH:1843-n100-ecc_Metadata.txt
        '''
        txt = sim_name.split(':')[-1]
        idx = int(txt[:4])
        res = int(txt.split('-')[1][1:])
        try:
            # If this works, its a quasicircular sim
            id_val = int(txt[-1])
            mf = self.metadata_file_fmts[0].format(idx, res, id_val)
        except:
            mf = self.metadata_file_fmts[1].format(idx, res)
        parts = mf.split(':')
        return "ExtrapStrain_" + parts[0] + "-" + parts[1] + "-" + parts[
            2].split('_')[0].split('-')[0] + "-" + parts[2].split(
                '_')[0].split('-')[1] + '.h5'

    def waveform_filename_from_cache(self, idx):
        mf = self.metadata_filename_from_cache(idx)
        sim_name = self.simname_from_metadata_filename(mf)
        return self.waveform_filename_from_simname(sim_name)

    def metadata_filenames(self, idx, res, id_val):
        return [
            self.metadata_file_fmts[0].format(idx, res, id_val),
            self.metadata_file_fmts[1].format(idx, res)
        ]

    def simname_from_cache(self, idx):
        possible_sim_tags = self.simtags(idx)
        for sim_tag in possible_sim_tags:
            mf = self.metadata_dir / sim_tag
            poss_files = glob.glob(str(mf) + "*")
            if len(poss_files) == 0:
                if self.verbosity > 4:
                    print(
                        "...found no files matching {}".format(str(mf) + "*"))
                continue
            file_path = poss_files[0]  # glob gives full paths
            file_name = os.path.basename(file_path)
            return self.simname_from_metadata_filename(file_name)
        return ''

    def simnames(self, idx, res, id_val):
        return [
            self.simname_from_metadata_filename(mf)
            for mf in self.metadata_filenames(idx, res, id_val)
        ]

    def simtags(self, idx):
        return [
            self.metadata_file_fmts[0].split('-')[0].format(idx),
            self.metadata_file_fmts[1].split('-')[0].format(idx)
        ]

    def sim_info_from_metadata_filename(self, file_name):
        return (int(file_name.split('-')[0][-4:]),
                int(file_name.split('-')[1][1:]),
                int(file_name.split('-')[2].split('_')[0][2:]))

    def get_metadata_from_link(self, link):
        requests.packages.urllib3.disable_warnings()
        for n in range(100):
            try:
                response = requests.get(link, verify=False)
                break
            except:
                continue
        return response.content.decode().split('\n')

    def parse_metadata_txt(self, raw):
        next = [s for s in raw if len(s) > 0 and s[0].isalpha()]
        opts = {}
        for s in next:
            kv = s.split('=')
            try:
                opts[kv[0].strip()] = float(kv[1].strip())
            except:
                opts[kv[0].strip()] = str(kv[1].strip())
        return next, opts

    def parse_metadata_fom_link(self, link):
        raw = self.get_metadata_from_link(link)
        return self.parse_metadata_txt(raw)

    def parse_metadata_from_file(self, file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
        return self.parse_metadata_txt(lines)

    def fetch_metadata(self, idx, res, id_val=-1):
        import pandas as pd
        possible_file_names = [
            self.metadata_file_fmts[0].format(idx, res, id_val),
            self.metadata_file_fmts[1].format(idx, res)
        ]
        metadata_txt, metadata_dict = "", {}
        sim = pd.DataFrame(metadata_dict)

        for file_name in possible_file_names:
            if self.verbosity > 2:
                print("...beginning search for {}".format(file_name))
            file_path_web = self.metadata_url + '/' + file_name
            mf = self.metadata_dir / file_name

            if self.use_cache:
                if os.path.exists(mf) and os.path.getsize(mf) > 0:
                    if self.verbosity > 2:
                        print("...reading from cache: {}".format(str(mf)))
                    metadata_txt, metadata_dict = self.parse_metadata_from_file(
                        mf)

            if len(metadata_dict) == 0:
                if url_exists(file_path_web):
                    if self.verbosity > 2:
                        print("...found {}".format(file_path_web))
                    metadata_txt, metadata_dict = self.parse_metadata_fom_link(
                        file_path_web)
                else:
                    if self.verbosity > 3:
                        print("...tried and failed to find {}".format(
                            file_path_web))

            if len(metadata_dict) > 0:
                break

        if len(metadata_dict) > 0:
            # Write to cache dir
            if self.use_cache and (not os.path.exists(mf)
                                   or os.path.getsize(mf) == 0):
                if self.verbosity > 1:
                    print("...writing to {}".format(mf))
                with open(mf, "w") as fout:
                    for line in metadata_txt:
                        fout.write(line + '\n')

            # Convert to DataFrame and write to disk
            metadata_dict['simulation_name'] = [
                self.simname_from_metadata_filename(file_name)
            ]
            metadata_dict['metadata_link'] = [file_path_web]
            metadata_dict['metadata_location'] = [mf]
            metadata_dict['waveform_data_location'] = [
                str(self.waveform_data_dir /
                    self.waveform_filename_from_simname(
                        metadata_dict['simulation_name'][0]))
            ]
            sim = pd.DataFrame.from_dict(metadata_dict)

        return sim

    def fetch_metadata_from_cache(self, idx):
        possible_sim_tags = self.simtags(idx)
        for sim_tag in possible_sim_tags:
            mf = self.metadata_dir / sim_tag
            poss_files = glob.glob(str(mf) + "*")
            if len(poss_files) == 0:
                if self.verbosity > 4:
                    print(
                        "...found no files matching {}".format(str(mf) + "*"))
                continue
            file_path = poss_files[0]  # glob gives full paths
            file_name = os.path.basename(file_path)
            file_path_web = self.metadata_url + '/' + file_name
            wf_file_name = self.waveform_filename_from_cache(idx)
            wf_file_path_web = self.waveform_data_url + '/' + wf_file_name
            _, metadata_dict = self.parse_metadata_from_file(file_path)
            if len(metadata_dict) > 0:
                metadata_dict['simulation_name'] = [
                    self.simname_from_metadata_filename(file_name)
                ]
                metadata_dict['metadata_link'] = [file_path_web]
                metadata_dict['metadata_location'] = [file_path]
                metadata_dict['waveform_data_link'] = [wf_file_path_web]
                metadata_dict['waveform_data_location'] = [
                    str(self.waveform_data_dir /
                        self.waveform_filename_from_simname(
                            metadata_dict['simulation_name'][0]))
                ]
                return pd.DataFrame.from_dict(metadata_dict)
        return pd.DataFrame({})

    def fetch_metadata_for_catalog(self,
                                   num_sims_to_crawl=100,
                                   possible_res=[],
                                   max_id_in_name=-1):
        '''
        We crawl the webdirectory where RIT metadata usually lives,
        and try to read metadata for as many simulations as we can
        '''
        if len(possible_res) == 0:
            possible_res = self.possible_res
        if max_id_in_name <= 0:
            max_id_in_name = self.max_id_val
        import pandas as pd
        sims = pd.DataFrame({})

        if self.use_cache:
            metadata_df_fpath = self.metadata_dir / "metadata.csv"
            if os.path.exists(metadata_df_fpath
                              ) and os.path.getsize(metadata_df_fpath) > 0:
                print("Opening file {}".format(metadata_df_fpath))
                self.metadata = pd.read_csv(metadata_df_fpath, index_col=[0])
                if len(self.metadata) >= (num_sims_to_crawl - 1):
                    # return self.metadata
                    return self.metadata.iloc[:num_sims_to_crawl - 1]
                else:
                    sims = self.metadata
        print(len(sims))

        for idx in range(1, 1 + num_sims_to_crawl):
            found = False
            possible_sim_tags = self.simtags(idx)

            if self.verbosity > 3:
                print("\nHunting for sim with idx: {}".format(idx))

            # First, check if metadata present as file on disk
            if not found and self.use_cache:
                if self.verbosity > 3:
                    print("checking for metadata file on disk")
                sim_data = self.fetch_metadata_from_cache(idx)
                if len(sim_data) > 0:
                    found = True
                    if self.verbosity > 3:
                        print("...metadata found on disk for {}".format(idx))

            # Second, check if metadata present already in DataFrame
            if len(sims) > 0 and not found:
                print("Checking existing dataframe")
                for _, row in sims.iterrows():
                    name = row['simulation_name']
                    for sim_tag in possible_sim_tags:
                        if sim_tag in name:
                            found = True
                            f_idx, res, id_val = self.sim_info_from_metadata_filename(
                                name)
                            assert f_idx == idx, """Index found for sim from metadata is not the same as we were searching for ({} vs {}).""".format(
                                f_idx, idx)
                            if self.verbosity > 3:
                                print("...metadata found in DF for {}, {}, {}".
                                      format(idx, res, id_val))
                            sim_data = pd.DataFrame.from_dict(row.to_dict(),
                                                              index=[0])
                            break

            # If not already present, fetch metadata the hard way
            if not found:
                for res in possible_res:
                    for id_val in range(max_id_in_name):
                        # If not already present, fetch metadata
                        sim_data = self.fetch_metadata(idx, res, id_val)
                        if len(sim_data) > 0:
                            found = True
                            if self.verbosity > 3:
                                print(
                                    "...metadata txt file found for {}, {}, {}"
                                    .format(idx, res, id_val))
                            break
                        else:
                            if self.verbosity > 3:
                                print("...metadata not found for {}, {}, {}".
                                      format(idx, res, id_val))
                    # just need to find one resolution, so exit loop if its been found
                    if found:
                        break
            if found:
                sims = pd.concat([sims, sim_data])
            else:
                if self.verbosity > 3:
                    print("...metadata for {} NOT FOUND.".format(
                        possible_sim_tags))

            self.metadata = sims
            if self.use_cache:
                self.write_metadata_df_to_disk()

        self.num_of_sims = len(sims)
        return self.metadata

    def write_metadata_df_to_disk(self):
        metadata_df_fpath = self.metadata_dir / "metadata.csv"
        with open(metadata_df_fpath, "w+") as f:
            self.metadata.to_csv(f)

    def refresh_metadata_df_on_disk(self, num_sims_to_crawl=2000):
        sims = []
        for idx in range(1, 1 + num_sims_to_crawl):
            sim_data = self.fetch_metadata_from_cache(idx)
            if len(sims) == 0:
                sims = sim_data
            else:
                sims = pd.concat([sims, sim_data])
        metadata_df_fpath = self.metadata_dir / "metadata.csv"
        with open(metadata_df_fpath, "w") as f:
            sims.to_csv(f)
        return sims

    def read_metadata_df_from_disk(self):
        metadata_df_fpath = self.metadata_dir / "metadata.csv"
        if os.path.exists(
                metadata_df_fpath) and os.path.getsize(metadata_df_fpath) > 0:
            self.metadata = pd.read_csv(metadata_df_fpath, index_col=[0])
        return self.metadata

    def download_waveform_data(self, sim_name, use_cache=None):
        '''
        Possible file formats:
        (1) https://ccrgpages.rit.edu/~RITCatalog/Data/ExtrapStrain_RIT-BBH-0193-n100.h5
        (2) https://ccrgpages.rit.edu/~RITCatalog/Data/ExtrapStrain_RIT-eBBH-1911-n100.h5
        '''
        if use_cache is None:
            use_cache = self.use_cache
        webdir = self.waveform_data_url

        file_name = self.waveform_filename_from_simname(sim_name)
        file_path_web = webdir + "/" + file_name
        local_file_path = self.waveform_data_dir / file_name
        if use_cache and os.path.exists(
                local_file_path) and os.path.getsize(local_file_path) > 0:
            if self.verbosity > 2:
                print("...can read from cache: {}".format(
                    str(local_file_path)))
            pass
        elif os.path.exists(
                local_file_path) and os.path.getsize(local_file_path) > 0:
            pass
        else:
            if self.verbosity > 2:
                print("...writing to cache: {}".format(str(local_file_path)))
            if url_exists(file_path_web):
                if self.verbosity > 2:
                    print("...downloading {}".format(file_path_web))
                # wget.download(str(file_path_web), str(local_file_path))
                import subprocess
                subprocess.call([
                    'wget', '--no-check-certificate',
                    str(file_path_web), '-O',
                    str(local_file_path)
                ])

            else:
                if self.verbosity > 2:
                    print("... ... but couldnt find link: {}".format(
                        str(file_path_web)))

    def fetch_waveform_data_from_cache(self, idx):
        wf = self.waveform_filename_from_cache(idx)
        wf_local_path = self.waveform_data_dir / wf
        raise NotImplementedError()

    def download_waveform_data_for_catalog(self,
                                           num_sims_to_crawl=100,
                                           possible_res=[],
                                           max_id_in_name=-1,
                                           use_cache=None):
        '''
        We crawl the webdirectory where RIT waveform data usually lives,
        and try to read waveform data for as many simulations as we can
        '''
        if len(possible_res) == 0:
            possible_res = self.possible_res
        if max_id_in_name <= 0:
            max_id_in_name = self.max_id_val
        if use_cache is None:
            use_cache = self.use_cache

        try:
            x = os.popen('/bin/ls {}/*.txt | wc -l'.format(
                str(self.metadata_dir)))
            num_metadata_txt_files = int(x.read().strip())
            x = os.popen('/bin/cat {}/metadata.csv | wc -l'.format(
                str(self.metadata_dir)))
            num_metadata_df = int(x.read().strip())
        except:
            # dummy values to force refresh below
            num_metadata_txt_files, num_metadata_df = 10, 0

        if num_metadata_df - 1 < num_metadata_txt_files:
            metadata = self.refresh_metadata_df_on_disk()
        else:
            metadata = self.read_metadata_df_from_disk()
        sims = {}

        for idx, sim_name in enumerate(metadata['simulation_name']):
            if idx + 1 > num_sims_to_crawl:
                break
            file_name = self.waveform_filename_from_simname(sim_name)
            local_file_path = self.waveform_data_dir / file_name
            self.download_waveform_data(sim_name, use_cache=use_cache)
            sims[sim_name] = local_file_path

        return sims
