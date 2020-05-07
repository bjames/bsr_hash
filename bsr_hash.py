import ipaddress
from pprint import pprint

from numpy import uint32, bitwise_and, bitwise_xor

def calculate_hash(rp_address, group, mask):

    """
        implements the has function from RFC 7761
    """

    result = uint32(bitwise_and(group,mask))
    result = uint32(uint32(1103515245) * uint32(result)) + uint32(12345)
    result = uint32(bitwise_xor(result, rp_address))
    result = uint32(uint32(1103515245) * uint32(result))
    result = uint32(uint32(result) + uint32(12345))
    result = uint32(uint32(result) % uint32(2**31))

    return result


if __name__ == '__main__':

    results = []
    rp_list = []
    group_list = []

    mask_length = uint32(input('mask length: '))
    rp_input = input('rp addresses (separated by spaces): ')

    for rp in rp_input.split():

         rp = ipaddress.IPv4Address(rp)
         rp_list.append(rp)

    start_group = ipaddress.IPv4Address(input('starting group: '))
    end_group = ipaddress.IPv4Address(input('ending group: '))

    while start_group <= end_group:
        group_list.append(start_group)
        start_group+=1

    mask = uint32((2**mask_length) - 1 << 32-mask_length)

    for group in group_list:

        group_result = []
        group_winner = ''
        winner_val = 0

        for rp in rp_list:

            value = calculate_hash(uint32(rp), uint32(group), mask)
            result = {
                'rp': str(rp),
                'value': value
            }

            if value > winner_val:
                winner_val = value
                group_winner = rp

            group_result.append(result)

        results.append({
            'group': group,
            'group_results': group_result,
            'group_winner': group_winner
        })


    print('OVERALL RESULTS\n')
    print('group\t', end='\t')

    for rp in rp_list:
        print(str(rp), end='\t')

    print()

    for group_result in results:
        print(group_result['group'], end='\t')
        for result in group_result['group_results']:
            print(result['value'], end='\t')
        print()

    print("\nWINNING RPs")

    print('\ngroup\twinner\tstreak')

    previous_result = ''
    streak = 1
    max_streak = 0
    winner_string = ''
    wins = [0] * len(rp_list)

    for group_result in results:

        if group_result['group_winner'] == previous_result:
            streak = streak + 1
        else:
            streak = 1
        if streak >= max_streak:
            max_streak = streak

        print("{}\t{}\t{}".format(str(group_result['group']), str(group_result['group_winner']), streak))

        winner_index = rp_list.index(group_result['group_winner'])
        wins[winner_index] += 1
        winner_string = winner_string + str(winner_index)

        if bitwise_and(uint32(group_result['group']), uint32(255)) == 255:
            winner_string = winner_string + '\n'

        previous_result = group_result['group_winner']

    print("max streak %r" %(max_streak))

    print('\nTOTAL WINS')

    print('rp\t\twins')
    for rp in rp_list:
        print("{}\t{}".format(str(rp), wins[rp_list.index(rp)]))

    print(winner_string)