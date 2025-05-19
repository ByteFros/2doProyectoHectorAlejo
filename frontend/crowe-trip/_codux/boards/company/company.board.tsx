import  Company  from '../../../src/components/company/company';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'Company',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <Company />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
