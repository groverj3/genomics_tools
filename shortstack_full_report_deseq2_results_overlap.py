#!/usr/bin/env python3

# Author: Jeffrey Grover
# Purpose: Find small RNA clusters from a ShortStack "full report" file that
# overlap with differentially expressed genes from DESeq2 results that have
# coordinate information added by deseq2_results_results_annotate.py
# Created: 10/2017

import csv
from argparse import ArgumentParser

# Parsing and overlap functions here


def parse_shortstack_full_report(input_report):
    shortstack_dict = {}
    with open(input_report, 'r') as input_handle:
        input_reader = csv.reader(input_handle)
        next(input_reader)
        for row in input_reader:
            chromosome = row[0].split(':')[0]
            cluster_start = int(row[0].split(':')[1].split('-')[0])
            cluster_stop = int(row[0].split(':')[1].split('-')[1])
            cluster_name = row[1]
            shortstack_info = row[2:]
            if chromosome not in shortstack_dict:
                shortstack_dict[chromosome] = {}
            if cluster_name not in shortstack_dict[chromosome]:
                shortstack_dict[chromosome][cluster_name] = [
                    cluster_start, cluster_stop
                ] + shortstack_info
    return shortstack_dict


def parse_deseq2_results(input_deseq2_results):
    results_dict = {}
    with open(input_deseq2_results, 'r') as input_handle:
        input_reader = csv.reader(input_handle)
        next(input_reader)
        for row in input_reader:
            chromosome = row[0]
            feature_id = row[1]
            feature_type = row[2]
            feature_start = int(row[3])
            feature_stop = int(row[4])
            deseq2_info = row[6:]
            if chromosome not in results_dict:
                results_dict[chromosome] = {}
            if feature_id not in results_dict[chromosome]:
                results_dict[chromosome][feature_id] = [
                    feature_start, feature_stop, feature_type
                ] + deseq2_info
    return results_dict


def overlap_shortstack_results(results_dict, shortstack_dict, upstream_bp,
                               downstream_bp, feature_body, output_file):
    overlap_header = ['upstream', 'body', 'downstream']
    upstream_overlaps = 0
    downstream_overlaps = 0
    body_overlaps = 0
    with open(output_file, 'w') as output_handle:
        output_writer = csv.writer(output_handle)
        output_writer.writerow(overlap_header)
        for chromosome in results_dict:
            if chromosome in shortstack_dict:
                for feature_id in results_dict[chromosome]:
                    feature_start = results_dict[chromosome][feature_id][0]
                    feature_stop = results_dict[chromosome][feature_id][1]
                    for cluster in shortstack_dict[chromosome]:
                        cluster_start = shortstack_dict[chromosome][cluster][0]
                        if upstream_bp > 0 and feature_start - upstream_bp <= cluster_start <= feature_start:
                            upstream_overlaps += 1
                        if feature_body and feature_start <= cluster_start <= feature_stop:
                            body_overlaps += 1
                        if downstream_bp > 0 and feature_stop + downstream_bp >= cluster_start >= feature_stop:
                            downstream_overlaps += 1
        overlaps = [upstream_overlaps, body_overlaps, downstream_overlaps]
        print(overlap_header)
        print(overlaps)
        output_writer.writerow(overlaps)


# Parse command line options

parser = ArgumentParser(
    description='Looks for overlap between features in a DESeq2 results file '
    'and siRNA clusters defined by ShortStack')
parser.add_argument(
    '--results',
    help='Input ShortStack Results file annotated with coordinates',
    metavar='File')
parser.add_argument(
    '--ssreport', help='Input ShortStack Report', metavar='File')
parser.add_argument(
    '--upstream',
    help='Distance upstream to look for overlap',
    type=int,
    default=0)
parser.add_argument(
    '--downstream',
    help='Distance downstream from gene to look for overlap',
    type=int,
    default=0)
parser.add_argument(
    '--body',
    help='Also look for overlap over the body of the feature',
    action='store_true',
    default=False)

results_file = parser.parse_args().results
ssreport = parser.parse_args().ssreport
upstream = parser.parse_args().upstream
body = parser.parse_args().body
downstream = parser.parse_args().downstream
overlap_file = ssreport.rsplit(
    '.', 1)[0] + ('_overlap_results_' + str(upstream) + '_up_' +
                  str(downstream) + '_down_' + str(body).lower() + '_body.csv')

# Run the functions to get the overlap

shortstack_dict = parse_shortstack_full_report(ssreport)
results_dict = parse_deseq2_results(results_file)

overlap_shortstack_results(results_dict, shortstack_dict, upstream, downstream,
                           body, overlap_file)
