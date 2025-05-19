import  Employee  from '../../../src/components/employee/employee';
import { ContentSlot, createBoard } from '@wixc3/react-board';
import { ComponentWrapper } from '_codux/wrappers/component-wrapper';

export default createBoard({
    name: 'Employee',
    Board: () => (
        <ComponentWrapper>
            <ContentSlot>
                <Employee />
            </ContentSlot>
        </ComponentWrapper>
    ),
});
