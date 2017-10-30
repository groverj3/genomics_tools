#!/usr/bin/env python3

# Author: Jeffrey Grover
# Purpose: Find small RNA clusters from a ShortStack "full report" file that
# overlap with features in a gtf or gff3
# Created: 10/2017

import csv
import random
from argparse import ArgumentParser
from itertools import groupby

# Parsing and overlap functions here


def get_chromosome_lengths(fasta_file):
    chr_lengths = []
    with open(fasta_file, 'r') as input_handle:
        for is_header, group in groupby(input_handle,
                                        lambda x: x.startswith('>')):
            if is_header:
                # Sequence header is the first line, only want chromosome name
                chromosome = next(group).strip('>').rstrip('\n')
            else:
                # Join the sequence lines due to wrapping and get their length
                seq_length = len(''.join(group).replace('\n', ''))
                record = [chromosome, seq_length]
                chr_lengths.append(record)
    return chr_lengths


def get_shortstack_clusters(loci_tsv):
    shortstack_loci = []
    with open(loci_tsv, 'r') as input_handle:
        reader = csv.reader(input_handle, delimiter='\t')
        next(reader)  # Skip header
        for row in reader:
            cluster_name = row[1]
            cluster_start = int(row[0].split(':')[1].split('-')[0])
            cluster_stop = int(row[0].split(':')[1].split('-')[1])
            cluster_length = cluster_stop - cluster_start
            cluster_record = [cluster_name, cluster_length]
            shortstack_loci.append(cluster_record)
    return shortstack_loci


def randomize_clusters(shortstack_loci, chr_lengths):
    randomized_clusters = {}
    for cluster in shortstack_loci:
        cluster_name = cluster[0]
        cluster_length = cluster[1]
        while True:  # Amateur hackiness
            random_record = random.choice(chr_lengths)
            chromosome = random_record[0]
            seq_length = random_record[1]
            if seq_length > cluster_length:
                break
        randomized_cluster_start = random.randint(0,
                                                  seq_length - cluster_length)
        randomized_cluster_stop = randomized_cluster_start + cluster_length
        if chromosome not in randomized_clusters:
            randomized_clusters[chromosome] = {}
        randomized_clusters[chromosome][cluster_name] = [
            randomized_cluster_start, randomized_cluster_stop,
            cluster_length
        ]
    return randomized_clusters


def parse_gtf(input_gtf, gtf_feature):
    gtf_dict = {}
    with open(input_gtf, 'r') as input_handle:
        input_reader = csv.reader(input_handle, delimiter='\t')
        for row in input_reader:
            if row[2] == gtf_feature:
                chromosome = row[0]
                start = int(row[3])
                stop = int(row[4])
                feature_id = str(row[8].split(';')[0])[8:]
                if chromosome not in gtf_dict:
                    gtf_dict[chromosome] = {}
                gtf_dict[chromosome][feature_id] = [start, stop]
        return gtf_dict


def parse_gff(input_gff, gff_feature):
    gff_dict = {}
    with open(input_gff, 'r') as input_handle:
        input_file = csv.reader(
            (row for row in input_handle if not row.startswith('#')),
            delimiter='\t')
        for row in input_file:
            if row[2] == gff_feature:
                chromosome = row[0]
                feature = row[2]
                start = int(row[3])
                stop = int(row[4])
                strand = row[6]
                feature_id = str(row[8].split(';')[0])[3:]
                if chromosome not in gff_dict:
                    gff_dict[chromosome] = {}
                gff_dict[chromosome][feature_id] = [start, stop]
        return gff_dict


def overlap_randomized_clusters(anno_dict, randomized_clusters, upstream_bp,
                                downstream_bp, feature_body):
    upstream_overlaps = 0
    downstream_overlaps = 0
    body_overlaps = 0
    for chromosome in gtf_dict:
        if chromosome in randomized_clusters:
            for feature_id in gtf_dict[chromosome]:
                feature_start = gtf_dict[chromosome][feature_id][0]
                feature_stop = gtf_dict[chromosome][feature_id][1]
                for cluster in randomized_clusters[chromosome]:
                    cluster_start = randomized_clusters[chromosome][cluster][0]
                    if upstream_bp > 0 and feature_start - upstream_bp <= cluster_start <= feature_start:
                        upstream_overlaps += 1
                    if feature_body and feature_start <= cluster_start <= feature_stop:
                        body_overlaps += 1
                    if downstream_bp > 0 and feature_stop + downstream_bp >= cluster_start >= feature_stop:
                        downstream_overlaps += 1
    return [upstream_overlaps, body_overlaps, downstream_overlaps]


def bootstrapper(loci_tsv, fasta_file, anno_file, feature, upstream_bp,
                 downstream_bp, feature_body, bootstraps, output_file):
    shortstack_loci = get_shortstack_clusters(loci_tsv)
    chr_lengths = get_chromosome_lengths(fasta_file)
    gtf_features = parse_gtf(anno_file, feature)
    overlap_header = ['upstream', 'body', 'downstream']
    with open(output_file, 'w') as output_handle:
        output_writer = csv.writer(output_handle)
        output_writer.writerow(overlap_header)
        for i in range(bootstraps):
            randomized_clusters = get_randomized_clusters(
                shortstack_loci, chr_lengths)
            overlaps = overlap_randomized_clusters(
                anno_dict, randomized_clusters, upstream_bp, downstream_bp,
                feature_body)
            print('Bootstrap' + str(i + 1) + ':', overlaps)
            output_writer.writerow(overlaps)
        print('Done!')


# Parse command line options

parser = ArgumentParser(
    description='Randomize shortstack loci and look for overlap with gtf '
    'features')
parser.add_argument(
    'a',
    'anno_type',
    help='Type of annotation, either gff3 or gtf',
    choices=('gff3', 'gtf'))
parser.add_argument(
    'g', 'anno_file', help='Input gff3 or gtf file', metavar='File')
parser.add_argument(
    'feature',
    help='Feature to look for overlap with from gtf3 file',
    type=str)
parser.add_argument(
    'ssloci', help='Input ShortStack loci file', metavar='File')
parser.add_argument('--fasta', help='Input genome fasta file', metavar='File')
parser.add_argument(
    'upstream',
    help='Distance upstream to look for overlap',
    type=int,
    default=0)
parser.add_argument(
    'downstream',
    help='Distance downstream from gene to look for overlap',
    type=int,
    default=0)
parser.add_argument(
    'body',
    help='Also look for overlap over the body of the feature',
    action='store_true',
    default=False)
parser.add_argument(
    'bootstraps',
    help='Number of randomization bootstraps to perform',
    type=int,
    default=1)

anno_type = parser.parse_args().anno_type
anno_file = parser.parse_args().anno_file
feature = parser.parse_args().feature
loci_tsv = parser.parse_args().ssloci
fasta_file = parser.parse_args().fasta
upstream = parser.parse_args().upstream
body = parser.parse_args().body
downstream = parser.parse_args().downstream
bootstraps = parser.parse_args().bootstraps
output_file = anno_file.split('.')[0] + (
    '_' + str(bootstraps) + '_bootstraps_random_' + feature + '_overlap_' +
    str(upstream) + '_up_' + str(downstream) + '_down_' + str(body).lower() +
    '_body.csv')

# Run the functions to get the overlap

if anno_type == 'gtf':
    bootstrapper(loci_tsv, fasta_file, anno_file, feature, upstream,
                 downstream, body, bootstraps, output_file)
elif anno_type == 'gff3':
    bootstrapper(loci_tsv, fasta_file, anno_file, feature, upstream,
                 downstream, body, bootstraps, output_file)
