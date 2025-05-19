import  TripManagerTab  from '../../../src/components/master/manage-companies/trip-manager-tab/trip-manager-tab';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'TripManagerTab',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <TripManagerTab />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
